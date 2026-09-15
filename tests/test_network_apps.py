"""Official editors, extensions and Salesforce CLI through a real proxy and TLS."""
import json
import os
import re
from pathlib import Path
import subprocess
import time
import unittest
import uuid

from test_commands import ROOT, command, docker

IMAGE = os.environ.get('WORKSTATION_SALESFORCE_TEST_IMAGE', 'electivus/webtop-arch-kde-salesforce:t06')
BASE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t06')


class ApplicationNetworkAcceptance(unittest.TestCase):
    def test_editors_extensions_and_salesforce_use_configured_network(self):
        resume = os.environ.get('WORKSTATION_NETWORK_TEST_RESUME', '')
        if resume and not re.fullmatch(r'ew-network-apps-[0-9a-f]{10}', resume):
            raise ValueError('resume requires the name of a retained network test fixture')
        name = resume or 'ew-network-apps-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        if resume:
            retained = json.loads((profile / 'retained-fixture.json').read_text(encoding='utf-8'))
            self.assertEqual(retained['name'], name)
            self.assertEqual(retained['network'], name + '-net')
            self.assertEqual(retained['fixture'], name + '-proxy')
        else:
            profile.mkdir(parents=True)
        network, fixture = name + '-net', name + '-proxy'
        succeeded = False
        try:
            if not resume:
                docker('network', 'create', network)
                docker('create', '--name', fixture, '--network', network, '--network-alias', 'network-target',
                       '--entrypoint', 'python3', BASE, '/tmp/network_fixture.py')
                docker('cp', str(ROOT / 'tests/network_fixture.py'), fixture + ':/tmp/network_fixture.py')
                docker('start', fixture)
            deadline = time.monotonic() + 30
            while subprocess.run(['docker', 'exec', fixture, 'test', '-f', '/tmp/network-fixture/ready'],
                                 capture_output=True).returncode:
                self.assertLess(time.monotonic(), deadline, 'TLS fixture startup')
                time.sleep(0.25)
            ca = profile / 'corporate-ca.crt'
            docker('cp', fixture + ':/tmp/network-fixture/trusted.crt', str(ca))
            config = profile / 'corporate-input.json'
            config.write_text(json.dumps({'proxy': 'http://' + fixture + ':3128', 'caFiles': [str(ca)]}), encoding='utf-8')
            cpus = str(min(4, int(docker('info', '--format', '{{.NCPU}}'))))
            if not resume:
                command('install', '--profile', profile, '--name', name, '--image', IMAGE, '--port', '13422',
                        '--memory', '6144', '--cpus', cpus, '--no-shortcut', '--network-config', config)
            command('start', '--profile', profile)
            if not resume:
                docker('network', 'connect', network, name)
            prepared = command('prepare', '--profile', profile)
            self.assertEqual(prepared['state'], 'completed')
            connections = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl')
            for domain in ['dl.google.com', 'packages.microsoft.com', 'registry.npmjs.org', 'marketplace.visualstudio.com']:
                self.assertIn(domain, connections, 'vendor preparation must use the configured proxy')
            docker('cp', str(ROOT / 'tests/network_probe'), name + ':/config/network_probe')
            docker('exec', name, 'chown', '-R', '1000:1000', '/config/network_probe')
            results = []
            for editor in ['code', 'code-insiders']:
                before = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
                receipt = '/config/' + editor + '-network.json'
                executed = subprocess.run(['docker', 'exec', '--user', 'abc', '--env', 'ELECTIVUS_TEST_RESULT=' + receipt,
                    name, 'timeout', '180', editor, '--wait', '--new-window', '--disable-workspace-trust',
                    '--skip-welcome', '--skip-release-notes', '--extensionDevelopmentPath=/config/network_probe',
                    '--extensionTestsPath=/config/network_probe/index.js', '/config/projects'],
                    capture_output=True, text=True, encoding='utf-8', timeout=210)
                (profile / (editor + '-network.log')).write_text(executed.stdout + executed.stderr, encoding='utf-8')
                docker('cp', name + ':' + receipt, str(profile / (editor + '-network.json')))
                result = json.loads((profile / (editor + '-network.json')).read_text(encoding='utf-8'))
                self.assertEqual(executed.returncode, 0, result)
                self.assertEqual(result['result'], 'passed')
                after = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
                self.assertGreater(after, before, editor + ' extension host must use the configured proxy')
                results.append(result)
            before_sf = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
            # This token is deliberately invalid and is sent only to our local TLS fixture.
            sf = subprocess.run(['docker', 'exec', '--user', 'abc', '--env', 'SF_ACCESS_TOKEN=00D000000000001!workstation-fixture-token',
                name, 'sf', 'org', 'login', 'access-token', '--instance-url', 'https://network-target:4443', '--no-prompt', '--json'],
                capture_output=True, text=True, encoding='utf-8', timeout=120)
            self.assertNotEqual(sf.returncode, 0)
            self.assertIn('NETWORK_FIXTURE_AUTH_REJECTED', sf.stdout + sf.stderr,
                          'Salesforce CLI must reach the HTTPS service and receive its intentional authentication rejection')
            after_sf = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
            self.assertGreater(after_sf, before_sf, 'Salesforce CLI must use the configured proxy')
            (profile / 'network-apps-result.json').write_text(json.dumps({'result': 'passed', 'editors': results,
                'vendorPreparationProxy': True, 'salesforceTLS': 'test service authentication rejection received',
                'salesforceProxy': True}, indent=2), encoding='utf-8')
            succeeded = True
        finally:
            if succeeded or os.environ.get('WORKSTATION_KEEP_FAILED_NETWORK') != '1':
                for container in [name, fixture]:
                    subprocess.run(['docker', 'container', 'rm', '--force', container], capture_output=True)
                subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
                subprocess.run(['docker', 'network', 'rm', network], capture_output=True)
            else:
                (profile / 'retained-fixture.json').write_text(json.dumps({'name': name, 'network': network,
                    'fixture': fixture, 'profile': str(profile)}, indent=2), encoding='utf-8')
                print('Retained owned network fixture: ' + str(profile))


if __name__ == '__main__':
    unittest.main()
