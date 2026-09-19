#!/usr/bin/env python3
"""Ask TypeSafe's Jev model a set of typed questions, then validate the answers.

The spec this reads IS the vendor request body:

    {"model": "jev-latest", "state": <string|object|array>, "questions": {...}}

Answers are checked against that spec before anything is reported. A response
that fails a fatal check becomes an error envelope; it is never reinterpreted,
retried against a loosened rule, or guessed at.

Requires Python 3.9+. Standard library only.
"""

import argparse
import hashlib
import http.client
import json
import math
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://api.typesafe.ai"
ENDPOINT_PATH = "/v1/systemone"
DEFAULT_MODEL = "jev-latest"
USER_AGENT = "jev-choice/1.0"

MAX_CHOICE_OPTIONS = 255
MIN_SCORE_LEVELS = 2
MAX_SCORE_LEVELS = 10
DEFAULT_MAX_STATE_BYTES = 120000
DEFAULT_TIMEOUT = 60.0
MAX_ATTEMPTS = 3
# 429 and 529 are documented. 503 is inherited from the client this was ported
# from, not from the contract; it is kept because it is harmless, not because
# the vendor promises it.
RETRY_STATUSES = (429, 529, 503)
ERROR_BODY_CHARS = 200

KIND_MISSING_KEY = "missing_key"
KIND_AUTHENTICATION = "authentication"
KIND_INVALID_REQUEST = "invalid_request"
KIND_RATE_LIMITED = "rate_limited"
KIND_OVERLOADED = "overloaded"
KIND_REDIRECT = "redirect"
KIND_TLS = "tls"
KIND_NETWORK = "network"
KIND_HTTP = "http"
KIND_INVALID_RESPONSE = "invalid_response"
KIND_VALIDATION = "validation"
KIND_BELOW_THRESHOLD = "below_threshold"


class JevError(Exception):
    """A failure worth reporting to the caller without a traceback."""

    def __init__(self, kind, message, status=None, request_id=None, detail=None):
        Exception.__init__(self, message)
        self.kind = kind
        self.message = message
        self.status = status
        self.request_id = request_id
        self.detail = detail


# --------------------------------------------------------------------------
# JSON helpers
# --------------------------------------------------------------------------


def reject_constant(name):
    """parse_constant hook: bare NaN/Infinity are not valid JSON."""
    raise ValueError("non-finite JSON literal %r" % (name,))


def unique_object(pairs):
    """object_pairs_hook: a duplicate key is corruption, not a last-wins edit."""
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate JSON key %r" % (key,))
        seen[key] = value
    return seen


def parse_json(raw, what):
    if raw.startswith("﻿"):
        raw = raw[1:]
    try:
        return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except ValueError as exc:
        raise JevError(KIND_INVALID_RESPONSE if what == "response" else KIND_INVALID_REQUEST,
                       "%s is not valid JSON: %s" % (what, exc))


def dump_json(payload):
    """Serialize for a pipe: no NaN, and bytes are written directly so a C
    locale cannot turn CJK into a UnicodeEncodeError."""
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=False)


def emit(payload, exit_code):
    sys.stdout.buffer.write(dump_json(payload).encode("utf-8") + b"\n")
    sys.stdout.buffer.flush()
    return exit_code


# --------------------------------------------------------------------------
# Numeric checks
# --------------------------------------------------------------------------


def is_number(value):
    """bool is a subclass of int, so `true` would otherwise pass as a
    probability. Do not relax this to isinstance()."""
    return type(value) in (int, float)


def is_finite_number(value):
    """Finiteness is checked before any comparison, because `nan < x` is False
    and would silently satisfy an inclusive range test."""
    return is_number(value) and math.isfinite(value)


def in_unit(value):
    return is_finite_number(value) and 0.0 <= value <= 1.0


# --------------------------------------------------------------------------
# Request-side validation (no network)
# --------------------------------------------------------------------------


def check_question(name, question):
    if not isinstance(question, dict):
        raise JevError(KIND_INVALID_REQUEST, "question %r is not an object" % name)
    kind = question.get("type")
    if kind not in ("choice", "score", "noul"):
        raise JevError(KIND_INVALID_REQUEST,
                       "question %r has type %r; expected choice, score, or noul" % (name, kind))
    instructions = question.get("instructions")
    if not isinstance(instructions, (str, dict, list)) or instructions == "":
        raise JevError(KIND_INVALID_REQUEST,
                       "question %r needs non-empty instructions (string, object, or array)" % name)
    criteria = question.get("criteria")
    if kind == "choice":
        if not isinstance(criteria, dict) or not criteria:
            raise JevError(KIND_INVALID_REQUEST, "choice question %r needs a criteria object" % name)
        if len(criteria) > MAX_CHOICE_OPTIONS:
            raise JevError(KIND_INVALID_REQUEST,
                           "choice question %r has %d options; the limit is %d"
                           % (name, len(criteria), MAX_CHOICE_OPTIONS))
    elif kind == "score":
        if not isinstance(criteria, list) or not all(isinstance(x, str) for x in criteria):
            raise JevError(KIND_INVALID_REQUEST,
                           "score question %r needs criteria as an ordered array of level descriptions" % name)
        if not MIN_SCORE_LEVELS <= len(criteria) <= MAX_SCORE_LEVELS:
            raise JevError(KIND_INVALID_REQUEST,
                           "score question %r has %d levels; the range is %d-%d"
                           % (name, len(criteria), MIN_SCORE_LEVELS, MAX_SCORE_LEVELS))
    elif criteria is not None:
        # noul takes an optional {"true": ..., "false": ...}.
        if not isinstance(criteria, dict) or not set(criteria) <= {"true", "false"}:
            raise JevError(KIND_INVALID_REQUEST,
                           "noul question %r may only carry criteria keys 'true' and 'false'" % name)


def check_spec(spec, max_state_bytes):
    if not isinstance(spec, dict):
        raise JevError(KIND_INVALID_REQUEST, "the spec must be a JSON object")
    unknown = set(spec) - {"model", "state", "questions"}
    if unknown:
        raise JevError(KIND_INVALID_REQUEST,
                       "unexpected top-level key(s): %s" % ", ".join(sorted(unknown)))
    if "state" not in spec:
        raise JevError(KIND_INVALID_REQUEST, "the spec needs a state")
    state = spec["state"]
    if not isinstance(state, (str, dict, list)):
        raise JevError(KIND_INVALID_REQUEST,
                       "state must be a string, object, or array (text only)")
    questions = spec.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise JevError(KIND_INVALID_REQUEST, "the spec needs a non-empty questions object")
    for name, question in questions.items():
        check_question(name, question)

    state_bytes = len(json.dumps(state, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    warnings = []
    if state_bytes > max_state_bytes:
        warnings.append(
            "state is %d bytes, above the %d-byte guideline; trim state unrelated to the "
            "decision, because irrelevant context degrades accuracy" % (state_bytes, max_state_bytes))
    return state_bytes, warnings


# --------------------------------------------------------------------------
# Response validation (driven by the spec)
# --------------------------------------------------------------------------


def validate_choice(question, answer, strict):
    """Fatal checks are contract guarantees; advisory ones are rounding
    sensitive and must not reject an otherwise valid answer."""
    fatal, warnings = [], []
    criteria = question["criteria"]
    choice = answer.get("choice")
    probabilities = answer.get("probabilities")

    if not isinstance(choice, str) or choice not in criteria:
        fatal.append("choice %r is not one of the offered options" % (choice,))
    if not isinstance(probabilities, dict):
        fatal.append("probabilities is missing or not an object")
        return fatal, warnings, None, None
    if set(probabilities) != set(criteria):
        fatal.append("probabilities cover %s, the offered options are %s"
                     % (sorted(probabilities), sorted(criteria)))
        return fatal, warnings, None, None
    for key, value in probabilities.items():
        if not in_unit(value):
            fatal.append("probability for %r is %r; expected a number in [0, 1]" % (key, value))
    confidence = answer.get("confidence")
    if not in_unit(confidence):
        fatal.append("confidence is %r; expected a number in [0, 1]" % (confidence,))
    if fatal:
        return fatal, warnings, None, None

    total = sum(probabilities.values())
    # The ported 0.02 was tuned for a handful of options; a ten-level score or a
    # wide choice set can drift further on rounded probabilities alone.
    tolerance = 0.02 if strict else max(0.02, 0.005 * len(probabilities))
    if abs(total - 1.0) > tolerance:
        warnings.append("probabilities sum to %.6f (tolerance %.4f)" % (total, tolerance))

    best = max(probabilities.values())
    # 1e-6, the ported value, sits below any plausible rounding quantum: an
    # unrounded near-tie can invert during rounding and reject a valid answer.
    slack = 1e-6 if strict else 0.005
    if probabilities[choice] < best - slack:
        rival = max(probabilities, key=lambda k: probabilities[k])
        warnings.append("chosen %r has %.6f but %r has %.6f; the server picked a non-argmax option"
                        % (choice, probabilities[choice], rival, best))
    return fatal, warnings, probabilities[choice], confidence


def validate_score(question, answer, strict):
    fatal, warnings = [], []
    levels = question["criteria"]
    expected = set(str(i) for i in range(len(levels)))
    probabilities = answer.get("probabilities")
    legend = answer.get("legend")
    score = answer.get("score")

    if not is_finite_number(score) or not 0 <= score <= len(levels) - 1:
        fatal.append("score is %r; expected a number from 0 to %d" % (score, len(levels) - 1))
    if not isinstance(probabilities, dict):
        fatal.append("probabilities is missing or not an object")
        return fatal, warnings, None, None
    if set(probabilities) != expected:
        fatal.append("probabilities cover %s; expected the level indices %s"
                     % (sorted(probabilities), sorted(expected)))
        return fatal, warnings, None, None
    for key, value in probabilities.items():
        if not in_unit(value):
            fatal.append("probability for level %r is %r; expected a number in [0, 1]" % (key, value))
    if legend is not None:
        if not isinstance(legend, dict):
            fatal.append("legend is not an object")
        elif set(legend) != set(probabilities):
            fatal.append("legend covers %s but probabilities cover %s"
                         % (sorted(legend), sorted(probabilities)))
        else:
            # Text equality is never fatal: the server may normalize or truncate,
            # and legend values are not guaranteed to be strings.
            for index, label in legend.items():
                if isinstance(label, str) and levels[int(index)] != label:
                    warnings.append("legend[%s] is %r but the request said %r"
                                    % (index, label, levels[int(index)]))
    confidence = answer.get("confidence")
    if not in_unit(confidence):
        fatal.append("confidence is %r; expected a number in [0, 1]" % (confidence,))
    if fatal:
        return fatal, warnings, None, None

    total = sum(probabilities.values())
    tolerance = 0.02 if strict else max(0.02, 0.005 * len(probabilities))
    if abs(total - 1.0) > tolerance:
        warnings.append("probabilities sum to %.6f (tolerance %.4f)" % (total, tolerance))

    expected_score = sum(int(k) * v for k, v in probabilities.items())
    if abs(score - expected_score) > 0.05:
        warnings.append("score %.4f differs from the probability-weighted position %.4f"
                        % (score, expected_score))
    return fatal, warnings, probabilities[str(int(round(score)))], confidence


def validate_noul(question, answer, strict):
    """noul answers carry a probability and nothing else: there is no
    confidence and no distribution to check."""
    fatal, warnings = [], []
    value = answer.get("noul")
    if not in_unit(value):
        fatal.append("noul is %r; expected a number in [0, 1]" % (value,))
        return fatal, warnings, None, None
    return fatal, warnings, value, None


VALIDATORS = {"choice": validate_choice, "score": validate_score, "noul": validate_noul}


def validate_answer(spec, answers, strict, min_confidence):
    """Pure function: no network, no I/O. Importable for testing."""
    questions = spec["questions"]
    if not isinstance(answers, dict):
        raise JevError(KIND_INVALID_RESPONSE, "the response has no answers object")

    missing = [name for name in questions if name not in answers]
    if missing:
        raise JevError(KIND_VALIDATION,
                       "the response omitted answers for: %s" % ", ".join(sorted(missing)))

    report = {}
    fatal_messages = []
    for name, question in questions.items():
        answer = answers[name]
        kind = question["type"]
        if not isinstance(answer, dict) or answer.get("type") != kind:
            got = answer.get("type") if isinstance(answer, dict) else type(answer).__name__
            fatal_messages.append("answer %r has type %r but the question asked for %r"
                                  % (name, got, kind))
            continue
        fatal, warnings, top_probability, confidence = VALIDATORS[kind](question, answer, strict)
        if fatal:
            fatal_messages.extend("answer %r: %s" % (name, m) for m in fatal)
            continue

        if kind == "noul":
            # The vendor returns no confidence for noul. Deriving one and
            # labelling the derivation is honest; passing it off as a vendor
            # value would not be.
            certainty = abs(answer["noul"] - 0.5) * 2.0
            basis = "derived_from_noul"
        else:
            certainty = confidence
            basis = "vendor"

        entry = {
            "type": kind,
            "certainty": certainty,
            "certainty_basis": basis,
            "warnings": warnings,
        }
        if top_probability is not None:
            entry["top_probability"] = top_probability
        if min_confidence is not None:
            entry["gate"] = {"min_confidence": min_confidence, "passed": certainty >= min_confidence}
        report[name] = entry

    if fatal_messages:
        raise JevError(KIND_VALIDATION, "; ".join(fatal_messages))
    return report


# --------------------------------------------------------------------------
# Credentials
# --------------------------------------------------------------------------


def credential_paths():
    home = os.path.expanduser("~")
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            yield os.path.join(appdata, "typesafe", "credentials.env")
    elif sys.platform == "darwin":
        yield os.path.join(home, "Library", "Application Support", "typesafe", "credentials.env")
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    yield os.path.join(xdg, "typesafe", "credentials.env")


def read_credential_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "TYPESAFE_API_KEY":
            value = value.strip().strip('"').strip("'")
            return value or None
    return None


def resolve_api_key():
    """Report which source supplied the key; never the key itself."""
    from_env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if from_env:
        return from_env, "environment (TYPESAFE_API_KEY)"
    for path in credential_paths():
        value = read_credential_file(path)
        if value:
            return value, path
    raise JevError(
        KIND_MISSING_KEY,
        "no TypeSafe API key found. Set TYPESAFE_API_KEY, or write "
        "TYPESAFE_API_KEY=<key> (one line, no quotes) to a credentials file at "
        + " or ".join(credential_paths())
        + " with mode 0600.")


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------


class RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """The endpoint answers a trailing-slash POST with a 307 that downgrades to
    plaintext http. Nothing here may follow a redirect, so the bearer token can
    never be re-sent to a host the caller did not name."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise JevError(KIND_REDIRECT,
                       "refusing to follow HTTP %s redirect to %r" % (code, headers.get("Location", newurl)))


OPENER = urllib.request.build_opener(RefuseRedirects)


def resolve_base_url():
    base = os.environ.get("TYPESAFE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not base.startswith("https://"):
        host = base.split("//", 1)[-1].split("/", 1)[0].split(":")[0]
        # TYPESAFE_BASE_URL exists so the error, retry, and redirect paths can be
        # exercised without a live key. Keep the exception narrow.
        if host not in ("localhost", "127.0.0.1", "[::1]", "::1"):
            raise JevError(KIND_INVALID_REQUEST,
                           "TYPESAFE_BASE_URL must be https, or http on localhost")
    return base


def describe_detail(body_text, content_type):
    try:
        parsed = json.loads(body_text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except ValueError:
        snippet = body_text[:ERROR_BODY_CHARS].replace("\n", " ")
        return "%s: %s" % (content_type or "unparseable body", snippet)
    if isinstance(parsed, dict) and "detail" in parsed:
        return parsed["detail"]
    return parsed


def post_once(url, key, body_bytes, timeout):
    request = urllib.request.Request(url, data=body_bytes, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", "Bearer " + key)
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", USER_AGENT)
    try:
        with OPENER.open(request, timeout=timeout) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as exc:
        # HTTPError *is* the response: read the body off the exception.
        return exc.code, exc.headers, exc.read()


def call_api(url, key, body_bytes, deadline):
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise JevError(KIND_NETWORK, "timed out after %.0fs" % DEFAULT_TIMEOUT)
        try:
            status, headers, raw = post_once(url, key, body_bytes, max(1.0, remaining))
        except JevError:
            raise
        except ssl.SSLCertVerificationError as exc:
            raise JevError(KIND_TLS,
                           "TLS certificate verification failed (%s). This Python has no usable "
                           "CA bundle; reinstall it or set SSL_CERT_FILE." % (exc,))
        except (OSError, http.client.HTTPException) as exc:
            # HTTPException is not an OSError, and a mid-body abort is OSError.
            last = JevError(KIND_NETWORK, "%s: %s" % (type(exc).__name__, exc))
            if attempt < MAX_ATTEMPTS:
                time.sleep(min(4.0, 0.5 * 2 ** (attempt - 1)) * (0.5 + random.random()))
                continue
            raise last

        request_id = headers.get("x-typesafe-request-id")
        if status < 400:
            return status, headers, raw, attempt, request_id

        detail = describe_detail(raw.decode("utf-8", "replace"), headers.get("content-type"))
        if status in (401, 403):
            raise JevError(KIND_AUTHENTICATION,
                           "the credential was rejected (HTTP %s). Check the key; do not retry."
                           % status, status=status, request_id=request_id, detail=detail)
        if status == 422:
            raise JevError(KIND_INVALID_REQUEST,
                           "the request body was rejected (HTTP 422). Fix the spec; do not retry.",
                           status=status, request_id=request_id, detail=detail)
        if status in RETRY_STATUSES:
            if attempt >= MAX_ATTEMPTS:
                kind = KIND_RATE_LIMITED if status == 429 else KIND_OVERLOADED
                raise JevError(kind, "HTTP %s after %d attempts" % (status, attempt),
                               status=status, request_id=request_id, detail=detail)
            delay = _retry_delay(headers, attempt)
            time.sleep(delay)
            continue
        raise JevError(KIND_HTTP, "HTTP %s" % status, status=status,
                       request_id=request_id, detail=detail)
    raise last if last else JevError(KIND_NETWORK, "no attempt was made")


def _retry_delay(headers, attempt):
    after = headers.get("Retry-After")
    if after:
        try:
            return max(0.0, min(30.0, float(after)))
        except ValueError:
            pass
    return min(4.0, 0.5 * 2 ** (attempt - 1)) * (0.5 + random.random())


def read_response_json(raw):
    text = raw.decode("utf-8", "replace")
    if text.startswith("﻿"):
        text = text[1:]
    try:
        parsed = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except ValueError as exc:
        raise JevError(KIND_INVALID_RESPONSE, "the response body is not valid JSON: %s" % (exc,))
    if not isinstance(parsed, dict) or "answers" not in parsed:
        raise JevError(KIND_INVALID_RESPONSE, "the response has no answers object")
    return parsed


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="jev_choose.py",
        description="Ask TypeSafe Jev typed questions and validate the answers against the request.")
    parser.add_argument("--spec", required=True,
                        help="path to the request spec (the vendor request body); '-' reads stdin")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate the spec, print the envelope, and send nothing")
    parser.add_argument("--strict", action="store_true",
                        help="restore the tighter ported tolerances for the advisory checks")
    parser.add_argument("--min-confidence", type=float, default=None,
                        help="flag answers whose certainty falls below this; does not change the exit code")
    parser.add_argument("--fail-below-threshold", action="store_true",
                        help="exit non-zero when --min-confidence is missed")
    parser.add_argument("--model", default=None, help="override the model id from the spec")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="total deadline for the call in seconds (default %(default)s)")
    parser.add_argument("--max-state-bytes", type=int, default=DEFAULT_MAX_STATE_BYTES,
                        help="warn above this state size (default %(default)s)")
    return parser


def load_spec(path):
    if path == "-":
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    else:
        try:
            with open(path, "rb") as handle:
                raw = handle.read().decode("utf-8", "replace")
        except OSError as exc:
            raise JevError(KIND_INVALID_REQUEST, "cannot read the spec at %s: %s" % (path, exc))
    if not raw.strip():
        raise JevError(KIND_INVALID_REQUEST, "the spec is empty")
    return parse_json(raw, "spec")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.min_confidence is not None and not 0.0 <= args.min_confidence <= 1.0:
        raise JevError(KIND_INVALID_REQUEST, "--min-confidence must be between 0 and 1")

    spec = load_spec(args.spec)
    state_bytes, request_warnings = check_spec(spec, args.max_state_bytes)

    model = args.model or spec.get("model") or os.environ.get("TYPESAFE_MODEL") or DEFAULT_MODEL
    body = {"model": model, "state": spec["state"], "questions": spec["questions"]}
    body_bytes = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")

    state_digest = hashlib.sha256(
        json.dumps(spec["state"], ensure_ascii=False, allow_nan=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    if args.dry_run:
        return emit({
            "ok": True,
            "dry_run": True,
            "model_requested": model,
            "request": body,
            "questions": sorted(spec["questions"]),
            "state_sha256": state_digest,
            "state_bytes": state_bytes,
            "warnings": request_warnings,
        }, 0)

    key, source = resolve_api_key()
    url = resolve_base_url() + ENDPOINT_PATH
    started = time.monotonic()
    deadline = started + args.timeout
    status, headers, raw, attempts, request_id = call_api(url, key, body_bytes, deadline)

    envelope = read_response_json(raw)
    report = validate_answer(spec, envelope["answers"], args.strict, args.min_confidence)

    warnings = list(request_warnings)
    gated = []
    for name, entry in report.items():
        warnings.extend("%s: %s" % (name, w) for w in entry["warnings"])
        gate = entry.get("gate")
        if gate and not gate["passed"]:
            gated.append(name)

    result = {
        "ok": True,
        "dry_run": False,
        "model_requested": model,
        "model": envelope.get("model"),
        "answers": envelope["answers"],
        "validation": report,
        "usage": envelope.get("usage"),
        "latency_ms": round((time.monotonic() - started) * 1000),
        "attempts": attempts,
        "request_id": request_id,
        "credential_source": source,
        "state_sha256": state_digest,
        "state_bytes": state_bytes,
        "warnings": warnings,
    }
    if gated:
        result["below_threshold"] = sorted(gated)
        if args.fail_below_threshold:
            result["ok"] = False
            result["kind"] = KIND_BELOW_THRESHOLD
            result["error"] = "certainty below --min-confidence for: %s" % ", ".join(sorted(gated))
            return emit(result, 1)
    return emit(result, 0)


def run(argv=None):
    try:
        return main(argv)
    except JevError as exc:
        payload = {"ok": False, "kind": exc.kind, "error": exc.message}
        if exc.status is not None:
            payload["status"] = exc.status
        if exc.request_id:
            payload["request_id"] = exc.request_id
        if exc.detail is not None:
            payload["detail"] = exc.detail
        return emit(payload, 1)
    except KeyboardInterrupt:
        return emit({"ok": False, "kind": KIND_NETWORK, "error": "interrupted"}, 1)


if __name__ == "__main__":
    sys.exit(run())
