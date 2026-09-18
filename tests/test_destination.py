"""Exercise the destination CMD guide without requiring Python on that destination."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid

from test_commands import ROOT, docker, invoke


@unittest.skipUnless(os.name == 'nt', 'Native Windows CMD guide')
class DestinationAcceptance(unittest.TestCase):
    def test_existing_evidence_is_preserved_and_missing_docker_is_diagnosed(self):
        with tempfile.TemporaryDirectory(prefix='destination-preflight-', dir=ROOT / '.local') as path:
            directory = Path(path)
            marker = directory / 'existing.txt'
            marker.write_text('keep this evidence')
            script = ROOT / 'distribution/windows/verify-target.cmd'
            refused = invoke(script, 'unused:tag', directory)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn('existing evidence is not overwritten', refused.stderr)
            self.assertEqual(marker.read_text(), 'keep this evidence')
            missing = directory / 'not-created'
            result = invoke(script, 'unused:tag', missing,
                            env=dict(os.environ, PATH=str(Path(os.environ['SystemRoot']) / 'System32')))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Docker CLI is unavailable', result.stderr)
            self.assertFalse(missing.exists())

    def test_cmd_guide_checks_applications_projects_and_recovery(self):
        image = os.environ['WORKSTATION_SALESFORCE_TEST_IMAGE']
        report = ROOT / '.local' / ('destination report ' + uuid.uuid4().hex[:10])
        arguments = [ROOT / 'distribution/windows/verify-target.cmd', image, report]
        if os.environ.get('WORKSTATION_TEST_NETWORK_CONFIG'):
            arguments.append(os.environ['WORKSTATION_TEST_NETWORK_CONFIG'])
        try:
            result = invoke(*arguments, timeout=5400)
            (ROOT / '.local' / 'destination-last-output.txt').write_text(result.stdout + result.stderr)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr + '\nReports: ' + str(report))
            self.assertEqual(json.loads((report / 'guest-checks.json').read_text())['state'], 'passed')
            self.assertTrue(json.loads((report / 'restored-project.json').read_text())['restoredProject'])
            state = json.loads((report / 'stop.json').read_text())
            self.assertEqual(state['state'], 'stopped')
            self.assertIn('remain pending', (report / 'result.txt').read_text())
            images = json.loads((report / 'image.json').read_text())
            self.assertEqual(images[0]['Id'], json.loads(docker('image', 'inspect', image))[0]['Id'])
            (ROOT / '.local' / 'destination-last-report.txt').write_text(str(report))
        finally:
            profile_path = report / 'profile/profile.json'
            if profile_path.is_file():
                profile = json.loads(profile_path.read_text())
                label = 'io.electivus.workstation.installation=' + profile['installationId']
                for kind in ('container', 'volume'):
                    selected = docker(kind, 'ls', *(['--all'] if kind == 'container' else []),
                                      '--quiet', '--filter', 'label=' + label).splitlines()
                    for identifier in selected:
                        subprocess.run(['docker', kind, 'rm', *(['--force'] if kind == 'container' else []),
                                        identifier], check=True, capture_output=True)


if __name__ == '__main__':
    (ROOT / '.local').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
