"""Corporate connectivity through CMD and actual TLS/proxy endpoints."""
import json
import os
import ssl
from pathlib import Path
import subprocess
import time
import unittest
import uuid

from test_commands import CLI, ROOT, command, docker, invoke

IMAGE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t06')


class NetworkAcceptance(unittest.TestCase):
    def test_preparation_retries_after_proxy_repair(self):
        name = 'ew-network-retry-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        profile.mkdir(parents=True)
        config = profile / 'corporate-input.json'
        network, fixture = name + '-net', name + '-proxy'
        config.write_text(json.dumps({'proxy': 'http://demo-user:p%40ss-test-123@' + fixture + ':3128'}), encoding='utf-8')
        try:
            docker('network', 'create', network)
            docker('create', '--name', fixture, '--network', network, '--env', 'WORKSTATION_TEST_PROXY_REFUSE=1',
                   '--entrypoint', 'python3', IMAGE, '/tmp/network_fixture.py')
            docker('cp', str(ROOT / 'tests/network_fixture.py'), fixture + ':/tmp/network_fixture.py')
            docker('start', fixture)
            deadline = time.monotonic() + 30
            while subprocess.run(['docker', 'exec', fixture, 'test', '-f', '/tmp/network-fixture/ready'],
                                 capture_output=True).returncode:
                self.assertLess(time.monotonic(), deadline, 'proxy fixture startup')
                time.sleep(0.25)
            command('install', '--profile', profile, '--name', name, '--image', IMAGE, '--port', '13421',
                    '--memory', '2560', '--cpus', '2', '--no-shortcut', '--network-config', config)
            command('start', '--profile', profile)
            docker('network', 'connect', network, name)
            failed = invoke(CLI, 'prepare', '--profile', profile)
            self.assertNotEqual(failed.returncode, 0, 'preparation must use the configured proxy')
            report = command('prepare', '--profile', profile, '--status')
            self.assertEqual(report['state'], 'failed')
            shared = failed.stdout + failed.stderr + json.dumps(report)
            for secret in ['demo-user', 'p%40ss-test-123', 'p@ss-test-123']:
                self.assertNotIn(secret, shared)
            self.assertEqual(report['app'], 'chrome')
            command('network', '--profile', profile, '--clear')
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            self.assertEqual(prepared['state'], 'completed')
            self.assertIn('chrome', prepared['apps'])
            self.assertNotIn('demo-user', docker('image', 'inspect', IMAGE))
            self.assertNotIn('demo-user', docker('history', '--no-trunc', IMAGE))
            (profile / 'network-retry-result.json').write_text(json.dumps({'result': 'passed',
                'failedApplication': report['app'], 'failedStep': report['step'], 'redaction': 'passed',
                'resumed': prepared['state']}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', name], capture_output=True)
            subprocess.run(['docker', 'container', 'rm', '--force', fixture], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            subprocess.run(['docker', 'network', 'rm', network], capture_output=True)

    def test_optional_proxy_and_trust(self):
        name = 'ew-network-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        profile.mkdir(parents=True)
        network, fixture = name + '-net', name + '-proxy'
        config = profile / 'corporate-input.json'
        config.write_text(json.dumps({'proxy': 'http://' + fixture + ':3128', 'caFiles': []}), encoding='utf-8')
        try:
            installed = command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                                '--port', '13420', '--memory', '2560', '--cpus', '2', '--no-shortcut',
                                '--network-config', config)
            self.assertEqual(installed['state'], 'installed')
            docker('network', 'create', network)
            docker('create', '--name', fixture, '--network', network, '--network-alias', 'network-target',
                   '--entrypoint', 'python3', IMAGE, '/tmp/network_fixture.py')
            docker('cp', str(ROOT / 'tests/network_fixture.py'), fixture + ':/tmp/network_fixture.py')
            docker('start', fixture)
            deadline = time.monotonic() + 30
            while subprocess.run(['docker', 'exec', fixture, 'test', '-f', '/tmp/network-fixture/ready'],
                                 capture_output=True).returncode:
                self.assertLess(time.monotonic(), deadline, 'TLS fixture startup')
                time.sleep(0.25)
            command('start', '--profile', profile)
            docker('network', 'connect', network, name)
            missing_ca = invoke(CLI, 'network', '--profile', profile, '--check', '--url', 'https://network-target:4443')
            self.assertNotEqual(missing_ca.returncode, 0)
            self.assertIn('tls', missing_ca.stdout.lower() + missing_ca.stderr.lower())
            ca = profile / 'corporate-ca.crt'
            docker('cp', fixture + ':/tmp/network-fixture/trusted.crt', str(ca))
            # Preserve a CA that the user had already trusted in the browser.
            nss = 'sql:/config/.local/share/pki/nssdb'
            docker('cp', str(ca), name + ':/tmp/previously-trusted.crt')
            docker('exec', '--user', 'abc', name, 'sh', '-c',
                   'mkdir -p /config/.local/share/pki/nssdb; test -f /config/.local/share/pki/nssdb/cert9.db || certutil -N --empty-password -d sql:/config/.local/share/pki/nssdb')
            docker('exec', '--user', 'abc', name, 'certutil', '-A', '-d', nss, '-t', 'C,,',
                   '-n', 'Previously trusted corporate CA', '-i', '/tmp/previously-trusted.crt')
            config.write_text(json.dumps({'proxy': 'http://' + fixture + ':3128', 'caFiles': [str(ca)]}), encoding='utf-8')
            changed = command('network', '--profile', profile, '--network-config', config)
            self.assertTrue(changed['restartRequired'])
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            proof = command('network', '--profile', profile, '--check', '--url', 'https://network-target:4443')
            self.assertEqual(proof['state'], 'connected')
            self.assertTrue(all(step['state'] == 'connected' for step in proof['checks']))
            before_terminal = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
            docker('exec', '--user', 'abc', name, 'zsh', '-lc', 'git ls-remote https://network-target:4443')
            after_terminal = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
            self.assertGreater(after_terminal, before_terminal, 'a fresh terminal must route Git through the configured proxy')
            self.assertEqual(command('prepare', '--profile', profile)['state'], 'completed')
            chrome = docker('exec', '--user', 'abc', name, 'timeout', '45', 'google-chrome', '--headless',
                            '--disable-gpu', '--user-data-dir=/tmp/network-chrome-valid', '--dump-dom', 'https://network-target:4443')
            self.assertIn('workstation-network-ok', chrome)
            after_chrome = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl').count('network-target')
            self.assertGreater(after_chrome, after_terminal, 'Chrome must use the configured proxy')
            rejected_chrome = docker('exec', '--user', 'abc', name, 'timeout', '45', 'google-chrome', '--headless',
                                     '--disable-gpu', '--user-data-dir=/tmp/network-chrome-invalid', '--dump-dom', 'https://network-target:4444')
            self.assertNotIn('workstation-network-ok', rejected_chrome)
            self.assertIn('ERR_CERT_AUTHORITY_INVALID', rejected_chrome)
            invalid = invoke(CLI, 'network', '--profile', profile, '--check', '--url', 'https://network-target:4444')
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn('tls', invalid.stdout.lower() + invalid.stderr.lower())
            connections = docker('exec', fixture, 'cat', '/tmp/network-fixture/connections.jsonl')
            self.assertIn('network-target', connections)
            roots = int(docker('exec', name, 'sh', '-c', "grep -c 'BEGIN CERTIFICATE' /etc/ssl/certs/ca-certificates.crt"))
            self.assertGreater(roots, 50, 'existing system roots remain available')
            command('network', '--profile', profile, '--clear')
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            state = command('network', '--profile', profile)
            self.assertFalse(state['proxyConfigured'])
            self.assertEqual(state['certificateCount'], 0)
            existing_ca = docker('exec', '--user', 'abc', name, 'certutil', '-L', '-d', nss,
                                 '-n', 'Previously trusted corporate CA', '-a')
            self.assertEqual(ssl.PEM_cert_to_DER_cert(existing_ca), ssl.PEM_cert_to_DER_cert(ca.read_text()))
            removed = invoke(CLI, 'network', '--profile', profile, '--check', '--url', 'https://network-target:4443')
            self.assertNotEqual(removed.returncode, 0)
            self.assertIn('tls', removed.stdout.lower() + removed.stderr.lower())
            (profile / 'network-result.json').write_text(json.dumps({'result': 'passed', 'checks': proof['checks'],
                'invalidTrustRejected': True, 'systemRootCount': roots, 'proxyConnections': len(connections.splitlines()),
                'configurationRemoved': True, 'existingBrowserCA': 'preserved',
                'terminalGitProxy': True, 'chromeProxyAndTLS': True}, indent=2), encoding='utf-8')
        finally:
            for container in [name, fixture]:
                subprocess.run(['docker', 'container', 'rm', '--force', container], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            subprocess.run(['docker', 'network', 'rm', network], capture_output=True)


if __name__ == '__main__':
    unittest.main()
