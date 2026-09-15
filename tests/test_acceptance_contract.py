"""Run a small real contract through the public acceptance command."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AcceptanceContract(unittest.TestCase):
    def test_unknown_variant_cannot_silently_validate_the_base_image(self):
        with tempfile.TemporaryDirectory(prefix='contract-', dir=ROOT / '.local') as directory:
            fixture = Path(directory)
            script = fixture / 'pass.py'
            script.write_text('print("would pass on the wrong image")\n', encoding='utf-8')
            contract = fixture / 'contract.json'
            contract.write_text(json.dumps({'schemaVersion': 1, 'checks': [
                {'id': 'wrong-variant', 'script': script.relative_to(ROOT).as_posix(), 'variant': 'saleforce'}]}), encoding='utf-8')
            result = subprocess.run([sys.executable, 'scripts/acceptance.py', '--contract', str(contract),
                                     '--output', str(fixture / 'results')], cwd=ROOT,
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((fixture / 'results' / 'acceptance.json').read_text(encoding='utf-8'))
            self.assertEqual(report['state'], 'failed')
            self.assertIn('variant', report['error'])
            self.assertFalse((fixture / 'results' / 'wrong-variant.log').exists())

    def test_success_runs_the_same_contract_with_each_selected_variant(self):
        with tempfile.TemporaryDirectory(prefix='contract-', dir=ROOT / '.local') as directory:
            fixture = Path(directory)
            script = fixture / 'variant.py'
            script.write_text('import os, sys\nassert os.environ["WORKSTATION_TEST_IMAGE"] == sys.argv[1]\n', encoding='utf-8')
            contract = fixture / 'contract.json'
            contract.write_text(json.dumps({'schemaVersion': 1, 'checks': [
                {'id': 'base', 'script': script.relative_to(ROOT).as_posix(), 'args': ['base:chosen']},
                {'id': 'salesforce', 'script': script.relative_to(ROOT).as_posix(), 'args': ['salesforce:chosen'],
                 'variant': 'salesforce'}]}), encoding='utf-8')
            result = subprocess.run([sys.executable, 'scripts/acceptance.py', '--contract', str(contract),
                                     '--output', str(fixture / 'results')], cwd=ROOT,
                                    env=dict(os.environ, WORKSTATION_TEST_IMAGE='base:chosen',
                                             WORKSTATION_SALESFORCE_TEST_IMAGE='salesforce:chosen'),
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads((fixture / 'results' / 'acceptance.json').read_text(encoding='utf-8'))
            self.assertEqual(report['state'], 'passed')
            self.assertEqual([check['state'] for check in report['checks']], ['passed', 'passed'])

    def test_failed_check_keeps_diagnostics_and_never_approves_the_candidate(self):
        with tempfile.TemporaryDirectory(prefix='contract-', dir=ROOT / '.local') as directory:
            fixture = Path(directory)
            (fixture / 'pass.py').write_text('print("working project")\n', encoding='utf-8')
            (fixture / 'fail.py').write_text('raise AssertionError("provided component is broken")\n', encoding='utf-8')
            (fixture / 'later.py').write_text('raise AssertionError("must not run")\n', encoding='utf-8')
            contract = fixture / 'contract.json'
            contract.write_text(json.dumps({'schemaVersion': 1, 'checks': [
                {'id': name, 'script': (fixture / f'{name}.py').relative_to(ROOT).as_posix()}
                for name in ('pass', 'fail', 'later')]}), encoding='utf-8')
            result = subprocess.run([sys.executable, 'scripts/acceptance.py', '--contract', str(contract),
                                     '--output', str(fixture / 'results')], cwd=ROOT,
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((fixture / 'results' / 'acceptance.json').read_text(encoding='utf-8'))
            self.assertEqual(report['state'], 'failed')
            self.assertEqual([check['state'] for check in report['checks']], ['passed', 'failed', 'not-run'])
            self.assertIn('provided component is broken', (fixture / 'results' / 'fail.log').read_text(encoding='utf-8'))
            self.assertFalse((fixture / 'results' / 'later.log').exists())


if __name__ == '__main__':
    (ROOT / '.local').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
