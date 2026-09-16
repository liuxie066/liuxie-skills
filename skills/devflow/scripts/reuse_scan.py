#!/usr/bin/env python3
"""Read-only reuse-candidate scanner for devflow Save Design.

Produces evidence only. It never decides whether a name should be reused: the
same name is not proof of the same semantic, and the same semantic often
carries different names. The ownership verdict stays with the agent
(see SKILL.md §2 step 3).

Two passes with different obligations:

* structure pass — reads every Python file it can and reports any it could not,
  because a partial owner inventory is not a valid "not found" result;
* text pass — a bounded keyword sweep, whose truncation is reported as a limit
  rather than a conclusion.

No writes, stdlib only, deterministic output for the same tree and revision.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "devflow.reuse_scan.v1"
DEFAULT_MAX_TEXT_FILES = 6000
DEFAULT_MAX_PYTHON_FILES = 20000
DEFAULT_MAX_FILE_BYTES = 2_000_000
MAX_TEXT_HIT_FILES = 40
MAX_RELATED_PER_QUERY = 25
MAX_GROUPS = 25
MAX_NAMES_IN_GROUP = 10
MAX_UNPARSED_REPORTED = 20

SKIP_DIRS = {
    "node_modules", "__pycache__", "venv", "env", "dist", "build", "target",
    "out", "site-packages", "htmlcov", "coverage", "vendor", "third_party",
}

TEXT_SUFFIXES = {
    ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sql", ".md",
    ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".kts", ".cs",
    ".rb", ".sh", ".proto", ".graphql",
}

# Directories that conventionally hold source rather than runtime artifacts.
# They are visited first so a bounded pass spends its budget on structure.
SOURCE_FIRST_DIRS = {
    "src", "domain", "app", "apps", "lib", "libs", "pkg", "packages",
    "internal", "cmd", "core", "api", "apis", "services", "service",
    "server", "client", "web", "ui", "tests", "test", "spec", "specs",
    "scripts", "bin", "tools", "proto", "controller", "handlers", "models",
}

# Tokens too generic to be near-synonym evidence on their own.
STOP_TOKENS = {
    "self", "none", "true", "false", "data", "info", "field", "fields",
    "value", "values", "name", "names", "type", "types", "kind", "kinds",
    "code", "codes", "list", "dict", "bool", "str", "int", "float",
    "optional", "default", "with", "from", "into", "that", "this", "when",
    "then", "else", "and", "the", "for", "not", "all", "any", "new", "old",
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only reuse-candidate scanner (evidence only, no verdicts)."
    )
    parser.add_argument("--root", default=".", help="repository root to scan (default: cwd)")
    parser.add_argument(
        "--query", action="append", default=[],
        help="a concept/name the design introduces; repeatable",
    )
    parser.add_argument(
        "--max-files", type=int, default=DEFAULT_MAX_TEXT_FILES,
        help="budget for the bounded text-keyword pass",
    )
    parser.add_argument(
        "--max-python-files", type=int, default=DEFAULT_MAX_PYTHON_FILES,
        help="safety valve for the structure pass; every Python file is expected to fit",
    )
    parser.add_argument(
        "--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES,
        help="skip text/source files larger than this",
    )
    parser.add_argument("--no-text", action="store_true", help="skip the text pass")
    parser.add_argument(
        "--include", action="append", default=[],
        help="glob limiting scanned relative paths (repeatable), e.g. --include 'domain/**'",
    )
    return parser.parse_args(argv)


def git_sha(root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and sha else None


def _dir_may_match(rel_dir: str, patterns: list[str]) -> bool:
    """True when a directory could still contain a path matching any pattern.
    Only a pruning hint for --include, never a correctness requirement."""
    if not patterns:
        return True
    probe = rel_dir + "/"
    for pattern in patterns:
        if fnmatch.fnmatch(probe, pattern):
            return True
        head = pattern.split("*", 1)[0].rstrip("/")
        if not head:
            return True
        if head == rel_dir or head.startswith(probe) or rel_dir.startswith(head + "/"):
            return True
    return False


def _walk(root: Path, patterns: list[str], only_suffix: str | None):
    """Yield (path, rel) in a stable, source-first order.

    Dot directories are skipped, which also keeps linked worktrees
    (e.g. .claude/worktrees) out of the scan.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        if rel_dir == ".":
            rel_dir = ""
        dirnames[:] = sorted(
            (
                name for name in dirnames
                if name not in SKIP_DIRS
                and not name.startswith(".")
                and _dir_may_match(f"{rel_dir}/{name}" if rel_dir else name, patterns)
            ),
            key=lambda name: (0 if name in SOURCE_FIRST_DIRS else 1, name),
        )
        for filename in sorted(
            name for name in filenames
            if (name.endswith(only_suffix) if only_suffix is not None
                else Path(name).suffix.lower() in TEXT_SUFFIXES)
        ):
            path = Path(dirpath) / filename
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if patterns and not any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                continue
            yield path, rel


def tokens(name: str) -> list[str]:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return [part for part in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if part]


def _class_level_names(node: ast.AST) -> list[tuple[str, str, int]]:
    found: list[tuple[str, str, int]] = []
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        found.append((node.target.id, "annotation", node.lineno))
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                found.append((target.id, "assignment", node.lineno))
    return found


class _DeclVisitor(ast.NodeVisitor):
    """Collects class-level names and string dict keys as structure evidence."""

    def __init__(self) -> None:
        self.classes: list[str] = []
        self.rows: list[tuple[str, str, str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        for child in node.body:
            for name, kind, line in _class_level_names(child):
                self.rows.append((node.name, name, kind, line))
        self.generic_visit(node)
        self.classes.pop()

    def visit_Dict(self, node: ast.Dict) -> None:
        owner = self.classes[-1] if self.classes else "<module>"
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value:
                self.rows.append(
                    (owner, key.value, "dict_key", getattr(key, "lineno", node.lineno))
                )
        self.generic_visit(node)


def collect_declarations(root: Path, patterns: list[str], limits: dict) -> dict:
    declarations: list[dict] = []
    unparsed: list[str] = []
    parsed = 0
    seen = 0
    oversized = 0
    skipped = 0
    for path, rel in _walk(root, patterns, only_suffix=".py"):
        if seen >= limits["max_python_files"]:
            skipped += 1
            continue
        try:
            if path.stat().st_size > limits["max_file_bytes"]:
                oversized += 1
                continue
        except OSError:
            continue
        seen += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            unparsed.append(rel)
            continue
        parsed += 1
        visitor = _DeclVisitor()
        visitor.visit(tree)
        for owner, name, kind, line in visitor.rows:
            declarations.append(
                {"path": rel, "owner": owner, "name": name, "kind": kind, "line": line}
            )
    return {
        "declarations": declarations,
        "python_seen": seen,
        "python_parsed": parsed,
        "python_unparsed": sorted(unparsed)[:MAX_UNPARSED_REPORTED],
        "python_skipped": skipped,
        "oversized_skipped": oversized,
    }


def owner_index(declarations: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    for row in declarations:
        index[row["name"]].append(row)
    return index


def shared_names(declarations: list[dict]) -> list[dict]:
    by_name: dict[str, set[str]] = defaultdict(set)
    paths: dict[str, set[str]] = defaultdict(set)
    for row in declarations:
        by_name[row["name"]].add(row["owner"])
        paths[row["name"]].add(row["path"])
    out = [
        {
            "name": name,
            "owners": sorted(owners)[:MAX_NAMES_IN_GROUP],
            "paths": sorted(paths[name])[:5],
            "owner_count": len(owners),
        }
        for name, owners in by_name.items()
        if len(owners) > 1
    ]
    out.sort(key=lambda row: (-row["owner_count"], row["name"]))
    return out[:MAX_GROUPS]


def synonym_groups(names: list[str]) -> list[dict]:
    by_token: dict[str, set[str]] = defaultdict(set)
    for name in names:
        for token in tokens(name):
            if len(token) >= 4 and token not in STOP_TOKENS:
                by_token[token].add(name)
    groups = [
        {"token": token, "count": len(found), "names": sorted(found)[:MAX_NAMES_IN_GROUP]}
        for token, found in by_token.items()
        if len(found) > 1
    ]
    groups.sort(key=lambda row: (-row["count"], row["token"]))
    return groups[:MAX_GROUPS]


def collect_text_hits(
    root: Path, patterns: list[str], queries: list[str], limits: dict
) -> tuple[dict, int, bool, int]:
    escaped = {
        query: re.compile(r"(?<![A-Za-z0-9_])" + re.escape(query) + r"(?![A-Za-z0-9_])")
        for query in queries
    }
    result: dict[str, dict] = {
        query: {"files": [], "total_matches": 0, "truncated": False} for query in queries
    }
    files_scanned = 0
    oversized = 0
    truncated = False
    for path, rel in _walk(root, patterns, only_suffix=None):
        if files_scanned >= limits["max_text_files"]:
            truncated = True
            continue
        try:
            if path.stat().st_size > limits["max_file_bytes"]:
                oversized += 1
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files_scanned += 1
        lines = text.splitlines()
        for query, pattern in escaped.items():
            count = 0
            first_line = 0
            for number, line in enumerate(lines, 1):
                if pattern.search(line):
                    count += 1
                    if not first_line:
                        first_line = number
            if not count:
                continue
            bucket = result[query]
            bucket["total_matches"] += count
            if len(bucket["files"]) < MAX_TEXT_HIT_FILES:
                bucket["files"].append({"path": rel, "count": count, "first_line": first_line})
            else:
                bucket["truncated"] = True
    return result, files_scanned, truncated, oversized


def build_query_reports(queries: list[str], index: dict[str, list[dict]], text_hits: dict) -> dict:
    names = sorted(index)
    reports: dict[str, dict] = {}
    for query in queries:
        exact = sorted(index.get(query, []), key=lambda row: (row["path"], row["line"]))
        query_tokens = {
            token for token in tokens(query)
            if len(token) >= 4 and token not in STOP_TOKENS
        }
        related = [
            {"name": name, "owners": sorted({row["owner"] for row in index[name]})[:5]}
            for name in names
            if name != query and query_tokens & set(tokens(name))
        ]
        reports[query] = {
            "exact_declarations": exact[:MAX_RELATED_PER_QUERY],
            "token_related_names": related[:MAX_RELATED_PER_QUERY],
            "text_hits": text_hits.get(
                query, {"files": [], "total_matches": 0, "truncated": False}
            ),
        }
    return reports


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: --root is not a directory: {root}", file=sys.stderr)
        return 2

    limits = {
        "max_text_files": args.max_files,
        "max_python_files": args.max_python_files,
        "max_file_bytes": args.max_file_bytes,
    }

    collected = collect_declarations(root, args.include, limits)
    declarations = collected["declarations"]
    index = owner_index(declarations)
    structure_truncated = collected["python_skipped"] > 0

    if structure_truncated:
        print(
            "warning: the structure pass hit its safety valve "
            f"(--max-python-files {args.max_python_files}); "
            f"{collected['python_skipped']} Python file(s) were not read, so the owner "
            "inventory is PARTIAL. Raise the valve or narrow with --include, and record "
            "the scanned range.",
            file=sys.stderr,
        )

    text_hits: dict = {}
    text_files_scanned = 0
    text_truncated = False
    text_oversized = 0
    if args.query and not args.no_text:
        text_hits, text_files_scanned, text_truncated, text_oversized = collect_text_hits(
            root, args.include, args.query, limits
        )

    notes = [
        "Evidence only: no reuse/new verdict is produced here.",
        "A shared name is not proof of shared semantics; a shared semantic often carries different names.",
        "Verify an owner by reading the cited symbol before recording `reuse <owner>` or `new`.",
    ]
    if structure_truncated:
        notes.append(
            "Owner inventory is partial: the structure pass skipped Python files. "
            "This is not an empty result."
        )
    if text_truncated:
        notes.append(
            "Text search is partial: the text budget was exhausted. It is not evidence "
            "that a hit does not exist."
        )

    report = {
        "schema": SCHEMA,
        "repo_root": str(root),
        "git_sha": git_sha(root),
        "scan": {
            "python_seen": collected["python_seen"],
            "python_parsed": collected["python_parsed"],
            "python_unparsed": collected["python_unparsed"],
            "python_skipped": collected["python_skipped"],
            "structure_truncated": structure_truncated,
            "text_files_scanned": text_files_scanned,
            "text_truncated": text_truncated,
            "oversized_skipped": collected["oversized_skipped"] + text_oversized,
            "max_python_files": args.max_python_files,
            "max_text_files": args.max_files,
            "max_file_bytes": args.max_file_bytes,
            "include": args.include,
        },
        "declared_name_across_owners": shared_names(declarations),
        "near_synonym_candidates": synonym_groups(list(index)),
        "queries": build_query_reports(args.query, index, text_hits),
        "notes": notes,
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
