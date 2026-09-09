"""Check one PRD's evidence record; never certify semantic correctness or change files."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


BLOCK = re.compile(r'^```prdflow-gate\s*\n(.*?)\n```[ \t]*$', re.M | re.S)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def fields(record, names, where):
    require(isinstance(record, dict), f'{where}: expected object')
    for name in names:
        require(nonempty(record.get(name)), f'{where}.{name}: required text')


def items(value, where):
    require(isinstance(value, list) and len(value) > 0, f'{where}: required nonempty list')
    return value


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse(document):
    blocks = list(BLOCK.finditer(document))
    require(len(blocks) == 1, 'Expected exactly one prdflow-gate fenced JSON block')
    block = blocks[0]
    record = json.loads(block[1], object_pairs_hook=unique_keys)
    require(isinstance(record, dict) and record.get('schema') == 'prdflow-gate.v1', 'Unknown gate schema')
    prose = document[:block.start()] + document[block.end():]
    # Bind the review to both the prose and all evidence, excluding only the review itself.
    payload = {'prose': prose, 'evidence': {k: v for k, v in record.items() if k != 'review'}}
    fingerprint = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return record, prose, fingerprint


def code_gate(code):
    fields(code, ['status', 'reason'], 'code')
    status = code['status']
    if status == 'not-applicable':
        require(code.get('basis') in ('new-project', 'non-software'), 'Code N/A needs new-project or non-software basis; unavailable is blocked')
        return
    require(status == 'pass', 'Code review is blocked or missing')
    fields(code, ['root', 'branch', 'revision', 'comparison', 'deployment', 'chain', 'findings', 'limits'], 'code')
    root = Path(code['root'])
    require(root.is_absolute() and root.is_dir(), 'Code root must be an existing absolute directory')
    if code['revision'] != 'no-git':
        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE, text=True).strip()
        if code['revision'] == 'unborn':
            git('rev-parse', '--git-dir')
            probe = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'], capture_output=True)
            require(probe.returncode != 0, 'Unborn baseline has a commit now; recheck code')
            require(git('symbolic-ref', '--short', 'HEAD') == code['branch'], 'Code branch drifted')
        else:
            require(git('rev-parse', 'HEAD') == code['revision'], 'Code HEAD drifted; recheck affected facts')
            require((git('branch', '--show-current') or 'detached') == code['branch'], 'Code branch drifted')
    else:
        probe = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True)
        require(probe.returncode != 0, 'no-git cannot bypass an existing Git baseline')
    files = items(code.get('files'), 'code.files')
    seen = set()
    for item in files:
        fields(item, ['path', 'sha256', 'role', 'finding'], 'code.files[]')
        relative = Path(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Code paths must be relative and contained')
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()) and path.is_file(), f'Missing/outside code file: {relative}')
        require(path not in seen, f'Duplicate code evidence: {relative}')
        seen.add(path)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Code content drifted: {relative}')


def check(document, phase):
    record, prose, fingerprint = parse(document)
    code_gate(record.get('code'))
    if phase == 'code':
        return 'code-evidence-checked'
    walkthroughs = items(record.get('walkthroughs'), 'walkthroughs')
    for row in walkthroughs:
        fields(row, ['scenario', 'input', 'result', 'exit'], 'walkthroughs[]')
        require(all(nonempty(s) for s in items(row.get('steps'), 'walkthroughs.steps')), 'Walkthrough steps require text')
    acceptance = items(record.get('acceptance'), 'acceptance')
    ids = set()
    for row in acceptance:
        fields(row, ['id', 'input', 'criterion', 'method', 'environment', 'mock_boundary', 'prerequisites', 'owner', 'evidence_status'], 'acceptance[]')
        require(row['id'] not in ids, 'Duplicate acceptance ID')
        ids.add(row['id'])
        require(row['evidence_status'] in ('planned', 'verified', 'unverified', 'failed'), 'Unknown acceptance evidence status')
        if row['evidence_status'] in ('verified', 'failed'):
            fields(row, ['evidence'], 'acceptance[]')
    temporal = record.get('temporal')
    fields(temporal, ['status', 'reason'], 'temporal')
    require(temporal['status'] in ('pass', 'not-applicable'), 'Temporal check blocked')
    if temporal['status'] == 'pass':
        for row in items(temporal.get('scenarios'), 'temporal.scenarios'):
            fields(row, ['sequence', 'final_state', 'must_not_recur'], 'temporal.scenarios[]')
    fields(record.get('research'), ['status', 'reason'], 'research')
    require(record['research']['status'] in ('pass', 'not-applicable'), 'Direction-changing research gap is unresolved')
    require(record.get('blockers') == [], 'Missing blocker disposition or unresolved blockers')
    review = record.get('review')
    fields(review, ['status', 'reviewer', 'method', 'rationale', 'content_sha256'], 'review')
    require(review['method'] in ('self-review', 'independent'), 'Review method must disclose actual independence')
    require(review['status'] == 'pass', 'Content review is missing, unusable or blocked')
    require(review['content_sha256'] == fingerprint, 'PRD/evidence changed after review')
    require(nonempty(prose), 'PRD prose is missing')
    return 'ready-record-checked; semantic judgment and user authorization remain separate'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prd', help='Markdown file, or - for stdin (no file writes)')
    parser.add_argument('--phase', choices=('code', 'ready'), default='ready')
    parser.add_argument('--fingerprint', action='store_true', help='print review fingerprint only; not a gate verdict')
    args = parser.parse_args()
    try:
        document = sys.stdin.read() if args.prd == '-' else Path(args.prd).read_text()
        if args.fingerprint:
            print(parse(document)[2])
        else:
            print(check(document, args.phase))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        print(f'BLOCKED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
