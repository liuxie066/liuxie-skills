"""Executable gate regressions; separate from agent behavior evaluations."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_gates.py'
spec = importlib.util.spec_from_file_location('check_gates', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def document(record, prose='# Packing checklist\nA1: The user can print a checklist.\n'):
    return prose + '\n```prdflow-gate\n' + json.dumps(record, ensure_ascii=False) + '\n```\n'


def signed(record):
    record = copy.deepcopy(record)
    record['review']['content_sha256'] = gate.parse(document(record))[2]
    return document(record)


def example():
    return {
        'schema': 'prdflow-gate.v1',
        'code': {'status': 'not-applicable', 'basis': 'non-software', 'reason': 'Paper checklist, no software'},
        'walkthroughs': [{'scenario': 'Pack', 'input': 'Three objects', 'steps': ['List objects', 'Print'], 'result': 'Visible list', 'exit': 'Take printed list'}],
        'acceptance': [{'id': 'A1', 'input': 'Three objects', 'criterion': 'All three visible', 'method': 'Inspect printed page', 'environment': 'Printer', 'mock_boundary': 'Preview cannot prove printed legibility', 'prerequisites': 'Printer access', 'owner': 'Product owner', 'evidence_status': 'planned'}],
        'temporal': {'status': 'not-applicable', 'reason': 'No retained system state'},
        'research': {'status': 'not-applicable', 'reason': 'No direction-changing external claim'},
        'blockers': [],
        'review': {'status': 'pass', 'reviewer': 'Fixture reviewer', 'method': 'self-review', 'rationale': 'Walked packing to printed result; physical check remains planned', 'content_sha256': ''},
    }


class GateTests(unittest.TestCase):
    def test_ready_cli_accepts_planned_external_acceptance_without_file_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPT), '-', '--phase', 'ready'], input=signed(example()), text=True, capture_output=True, cwd=directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_missing_unusable_and_stale_records_fail_closed(self):
        base = example()
        bad = []
        for key in ('code', 'walkthroughs', 'acceptance', 'temporal', 'research', 'blockers', 'review'):
            r = copy.deepcopy(base)
            del r[key]
            bad.append(document(r))
        for key in ('method', 'environment', 'mock_boundary', 'criterion', 'input', 'prerequisites', 'owner'):
            r = copy.deepcopy(base)
            del r['acceptance'][0][key]
            bad.append(signed(r))
        for key in ('code', 'temporal', 'research', 'review'):
            r = copy.deepcopy(base)
            r[key]['status'] = 'blocked'
            bad.append(signed(r))
        r = copy.deepcopy(base)
        r['blockers'] = ['No matching source']
        bad.append(signed(r))
        r = copy.deepcopy(base)
        r['acceptance'][0]['evidence_status'] = 'verified'
        bad.append(signed(r))
        r = copy.deepcopy(base)
        r['acceptance'].append(r['acceptance'][0])
        bad.append(signed(r))
        r = copy.deepcopy(base)
        r['code']['basis'] = 'repository-unavailable'
        bad.append(signed(r))
        bad.extend([signed(base).replace('Three objects', 'Four objects'), signed(base).replace('Packing checklist', 'Different goal'), document(base), '{}', signed(base) + signed(base), '```prdflow-gate\n{invalid}\n```'])
        for draft in bad:
            with self.subTest(draft=draft[:90]):
                with self.assertRaises((ValueError, TypeError)):
                    gate.check(draft, 'ready')

    def test_stateful_scenario_requires_final_and_non_recurrence(self):
        r = example()
        r['temporal'] = {'status': 'pass', 'reason': 'Preference survives sessions', 'scenarios': [{'sequence': 'Save then correct then reopen', 'final_state': 'Corrected value', 'must_not_recur': 'Original preference'}]}
        self.assertIn('ready-record-checked', gate.check(signed(r), 'ready'))
        del r['temporal']['scenarios'][0]['must_not_recur']
        with self.assertRaises(ValueError):
            gate.check(signed(r), 'ready')

    def test_code_phase_checks_read_file_bytes_and_rejects_fake_no_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / 'entry.py'
            source.write_text('def lookup(): return "retained receipt"\n')
            r = {'schema': 'prdflow-gate.v1', 'code': {'status': 'pass', 'reason': 'Entry read', 'root': str(root), 'branch': 'no-git', 'revision': 'no-git', 'comparison': 'No repository metadata', 'deployment': 'Not checked', 'chain': 'lookup -> retained receipt', 'findings': 'Read already implemented', 'limits': 'No production data checked', 'files': [{'path': 'entry.py', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'role': 'Entry', 'finding': 'Returns retained receipt'}]}}
            self.assertEqual(gate.check(document(r), 'code'), 'code-evidence-checked')
            source.write_text('def lookup(): return None\n')
            with self.assertRaisesRegex(ValueError, 'drifted'):
                gate.check(document(r), 'code')
            r['code']['files'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            with self.assertRaisesRegex(ValueError, 'no-git'):
                gate.check(document(r), 'code')
            r['code']['revision'] = 'unborn'
            r['code']['branch'] = subprocess.check_output(['git', '-C', str(root), 'symbolic-ref', '--short', 'HEAD'], text=True).strip()
            self.assertEqual(gate.check(document(r), 'code'), 'code-evidence-checked')

    def test_duplicate_json_cannot_hide_blocker_or_forge_review(self):
        for draft in (signed(example()).replace('"blockers": []', '"blockers": ["unresolved"], "blockers": []'), signed(example()).replace('"status": "pass"', '"status": "blocked", "status": "pass"')):
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
                gate.check(draft, 'ready')

    def test_malformed_cli_returns_nonzero_without_traceback(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '-'], input='```prdflow-gate\n{}\n```', capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('BLOCKED', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
