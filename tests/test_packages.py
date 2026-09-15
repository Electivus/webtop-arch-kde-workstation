"""Persistent extra-package inventory and assisted recovery through public commands."""
import json
import os
import re
import subprocess
import time
import unittest
import uuid

from test_commands import ROOT, CLI, command, docker, invoke
from test_backups import discard_backup_archives

IMAGE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t08')


def configure_test_network(profile):
    if os.environ.get('WORKSTATION_TEST_CA_FILE'):
        network = profile / 'package-network.json'
        network.write_text(json.dumps({'caFiles': [os.environ['WORKSTATION_TEST_CA_FILE']]}), encoding='utf-8')
        command('network', '--profile', profile, '--network-config', network)


def write_build_source(name, source, content):
    docker('exec', '--user', 'abc', name, 'python3', '-c',
           'from pathlib import Path; import hashlib,sys; p=Path(sys.argv[1]); '
           'c=p/"example.c"; old=c.read_bytes(); new=sys.argv[2].encode(); c.write_bytes(new); '
           'recipe=p/"PKGBUILD"; recipe.write_text(recipe.read_text().replace('
           'hashlib.sha256(old).hexdigest(), hashlib.sha256(new).hexdigest()))', source, content)


def install_local_fixture(name, source, package='workstation-local-example', dependency=False):
    docker('exec', '--user', 'abc', name, 'mkdir', '-p', source)
    docker('cp', str(ROOT / 'tests/fixtures/extra-package') + '/.', name + ':' + source)
    docker('exec', name, 'chown', '-R', 'abc:abc', source)
    if package != 'workstation-local-example':
        docker('exec', '--user', 'abc', name, 'python3', '-c',
               'from pathlib import Path; import sys; p=Path(sys.argv[1])/"PKGBUILD"; '
               'p.write_text(p.read_text().replace("workstation-local-example", sys.argv[2]))', source, package)
        content = (ROOT / 'tests/fixtures/extra-package/example.c').read_text().replace('workstation local example', package)
        write_build_source(name, source, content)
    reason = ['--asdeps'] if dependency else []
    docker('exec', '--user', 'abc', name, 'workstation-network', 'exec', '--',
           'makepkg', '--dir', source, '--force', '--noconfirm', '--install', *reason)


class PackageAcceptance(unittest.TestCase):
    def test_explicit_dependency_survives_recursive_removal_after_recovery(self):
        self.assert_explicit_dependency_recovery()

    def test_failed_reason_reconciliation_keeps_explicit_choices_for_retry(self):
        self.assert_explicit_dependency_recovery(interrupt=True)

    def assert_explicit_dependency_recovery(self, interrupt=False):
        name = 'ew-packages-explicit-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        selected = ['httpie', 'python-requests-toolbelt']
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13450', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            docker('exec', name, 'workstation-network', 'exec', '--', 'pacman', '-Syu', '--needed',
                   '--disable-download-timeout', '--noprogressbar', '--noconfirm', *selected)
            original = {entry['name']: entry for entry in command('packages', '--profile', profile)['extras']}
            for package in selected:
                self.assertEqual(original[package]['reason'], 'explicit')
            command('stop', '--profile', profile)
            docker('container', 'rm', name)
            command('start', '--profile', profile)
            if interrupt:
                # A real pacman post-transaction hook injects a stale database
                # lock after HTTPie has pulled toolbelt in as a dependency.
                # Pacman itself must reject the following metadata transaction.
                docker('cp', str(ROOT / 'tests/package_reason_lock_fixture.py'),
                       name + ':/tmp/package_reason_lock_fixture.py')
                hook = ('[Trigger]\nOperation = Install\nType = Package\nTarget = httpie\n\n'
                        '[Action]\nWhen = PostTransaction\n'
                        'Exec = /usr/bin/python3 /tmp/package_reason_lock_fixture.py\n')
                docker('exec', name, 'python3', '-c',
                       'from pathlib import Path; import sys; '
                       'Path("/etc/pacman.d/hooks/99-test-reason-lock.hook").write_text(sys.argv[1])', hook)
                rejected = invoke(CLI, 'packages', '--profile', profile, '--restore')
                docker('exec', name, 'test', '-f', '/tmp/package-reason-lock-injected')
                self.assertNotEqual(rejected.returncode, 0, rejected.stdout)
                self.assertIn('Could not restore saved package installation reasons', rejected.stderr)
                self.assertIn('unable to lock database', rejected.stderr)
                (profile / 'reconciliation-failure.txt').write_text(rejected.stderr, encoding='utf-8')
                interrupted_inventory = command('packages', '--profile', profile)
                (profile / 'interrupted-inventory.json').write_text(
                    json.dumps(interrupted_inventory, indent=2), encoding='utf-8')
                # A fresh container discards the injected lock and the test hook;
                # only the user's persistent inventory can carry the intent.
                command('stop', '--profile', profile)
                docker('container', 'rm', name)
                command('start', '--profile', profile)
            result = command('packages', '--profile', profile, '--restore')
            self.assertEqual(result['state'], 'completed', result)
            restored = {entry['name']: entry for entry in command('packages', '--profile', profile)['extras']}
            # httpie sorts first and installs toolbelt as a dependency. The
            # user's separately selected toolbelt must survive removing httpie.
            docker('exec', name, 'pacman', '-Rs', '--noconfirm', 'httpie')
            remaining = subprocess.run(['docker', 'exec', '--user', 'abc', name, 'python3', '-c',
                'import requests_toolbelt; print(requests_toolbelt.__version__)'], capture_output=True, text=True)
            (profile / 'explicit-dependency-result.json').write_text(json.dumps({'restoration': result,
                'retriedAfterDatabaseLockFailureAndRecreation': interrupt,
                'selectedReasons': {package: restored[package]['reason'] for package in selected},
                'toolbeltAfterRecursiveRemovalExit': remaining.returncode,
                'toolbeltAfterRecursiveRemoval': remaining.stdout.strip()}, indent=2), encoding='utf-8')
            for package in selected:
                self.assertEqual(restored[package]['reason'], 'explicit', restored[package])
            self.assertEqual(remaining.returncode, 0, remaining.stderr)
            self.assertTrue(remaining.stdout.strip())
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_makepkg_dependency_installation_uses_the_profile_proxy_after_sudo(self):
        name = 'ew-packages-proxy-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        source = '/config/projects/proxy-build'
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13449', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            install_local_fixture(name, source)
            config = profile / 'package-network.json'
            settings = {'proxy': 'http://127.0.0.1:31281'}
            if os.environ.get('WORKSTATION_TEST_CA_FILE'):
                settings['caFiles'] = [os.environ['WORKSTATION_TEST_CA_FILE']]
            config.write_text(json.dumps(settings), encoding='utf-8')
            command('network', '--profile', profile, '--network-config', config)
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            docker('cp', str(ROOT / 'tests/package_proxy_fixture.py'), name + ':/tmp/package_proxy_fixture.py')
            docker('exec', '--detach', '--user', 'abc', name, 'python3', '/tmp/package_proxy_fixture.py')
            deadline = time.monotonic() + 10
            while subprocess.run(['docker', 'exec', name, 'test', '-f', '/tmp/package-proxy/ready'],
                                 capture_output=True).returncode:
                self.assertLess(time.monotonic(), deadline, 'package proxy fixture startup')
                time.sleep(0.1)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; import sys; p=Path(sys.argv[1])/"PKGBUILD"; '
                   'p.write_text(p.read_text().replace("makedepends=(\'gcc\')", "makedepends=(\'gcc\' \'figlet\')"))', source)
            attempted = subprocess.run(['docker', 'exec', '--user', 'abc', name, 'workstation-network', 'exec', '--',
                'makepkg', '--dir', source, '--force', '--cleanbuild', '--syncdeps', '--noconfirm'],
                capture_output=True, text=True, encoding='utf-8', timeout=90)
            diagnostic = attempted.stdout + attempted.stderr
            requests = [json.loads(line) for line in docker('exec', name, 'cat',
                        '/tmp/package-proxy/connections.jsonl').splitlines()]
            (profile / 'package-proxy-result.json').write_text(json.dumps({'exit': attempted.returncode,
                'requests': requests, 'diagnostic': diagnostic}, indent=2), encoding='utf-8')
            self.assertNotEqual(attempted.returncode, 0, diagnostic)
            self.assertIn('figlet', diagnostic)
            self.assertIn('502', diagnostic, diagnostic)
            mirrors = re.findall(r"from ([^\s:]+) :", diagnostic)
            self.assertTrue(any(mirror in request['target'] for mirror in mirrors for request in requests),
                            {'mirrors': mirrors, 'requests': requests, 'diagnostic': diagnostic})
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_concurrent_source_registrations_preserve_both_package_records(self):
        name = 'ew-packages-concurrent-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        operations = []
        sources = [('workstation-local-example', '/config/projects/source-a', 'a', 'b'),
                   ('workstation-local-second', '/config/projects/source-b', 'b', 'a')]
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13448', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            for package, source, own, peer in sources:
                install_local_fixture(name, source, package)
                # Source inspection can take time. Coordinate real PKGBUILD
                # evaluations so both registrations inspect their sources together.
                barrier = ('\nif [[ -f /config/projects/registration-race-active ]]; then\n'
                           '    touch /config/projects/registration-ready-' + own + '\n'
                           '    while [[ ! -f /config/projects/registration-ready-' + peer + ' ]]; do sleep 0.05; done\n'
                           'fi\n')
                docker('exec', '--user', 'abc', name, 'python3', '-c',
                       'from pathlib import Path; import sys; p=Path(sys.argv[1])/"PKGBUILD"; '
                       'p.write_text(p.read_text()+sys.argv[2])', source, barrier)
            docker('exec', '--user', 'abc', name, 'touch', '/config/projects/registration-race-active')
            for package, source, _, _ in sources:
                operations.append(subprocess.Popen(['docker', 'exec', '--user', 'root', name,
                    'workstation-packages', 'register', '--package', package, '--source', source],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'))
            for operation in operations:
                output, diagnostic = operation.communicate(timeout=60)
                self.assertEqual(operation.returncode, 0, diagnostic)
                json.loads(output)
            inventory = command('packages', '--profile', profile)
            extras = {entry['name']: entry for entry in inventory['extras']}
            (profile / 'concurrent-sources-result.json').write_text(json.dumps(extras, indent=2), encoding='utf-8')
            for package, source, _, _ in sources:
                for target in [package, package + '-debug']:
                    self.assertIn('source', extras[target], extras)
                    self.assertEqual(extras[target]['source']['directory'], source)
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for operation in operations:
                if operation.poll() is None:
                    operation.communicate(timeout=30)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_backup_recovers_inventory_sources_and_the_ability_to_restore_extras(self):
        name = 'ew-packages-backup-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        source = '/config/projects/backed-up-build'
        inventory_file = '/config/.local/state/electivus/packages.json'
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13447', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            docker('exec', name, 'workstation-network', 'exec', '--', 'pacman', '-Syu', '--needed',
                   '--disable-download-timeout', '--noprogressbar', '--noconfirm', 'figlet')
            install_local_fixture(name, source)
            command('packages', '--profile', profile, '--register', 'workstation-local-example', '--source', source)
            original = json.loads(docker('exec', '--user', 'abc', name, 'cat', inventory_file))['extras']
            saved = command('backup', '--profile', profile)
            command('start', '--profile', profile)
            docker('exec', name, 'pacman', '-R', '--noconfirm', 'figlet',
                   'workstation-local-example', 'workstation-local-example-debug')
            write_build_source(name, source, '#error changed after backup\n')
            current = command('packages', '--profile', profile)
            self.assertNotIn('workstation-local-example', {entry['name'] for entry in current['extras']})
            recovered = command('restore', '--profile', profile, '--backup', saved['directory'])
            self.assertEqual(recovered['state'], 'restored')
            command('start', '--profile', profile)
            records = json.loads(docker('exec', '--user', 'abc', name, 'cat', inventory_file))['extras']
            self.assertEqual(records, original)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', source + '/example.c'),
                             (ROOT / 'tests/fixtures/extra-package/example.c').read_text().strip())
            missing = command('packages', '--profile', profile)
            self.assertEqual(missing['state'], 'partial')
            restored = command('packages', '--profile', profile, '--restore')
            self.assertEqual(restored['state'], 'completed', restored)
            self.assertEqual(docker('exec', name, 'workstation-local-example'), 'workstation local example')
            docker('exec', name, 'figlet', 'recovered')
            (profile / 'package-backup-result.json').write_text(json.dumps({'result': 'passed',
                'backup': saved, 'recovery': recovered, 'inventory': records, 'restoration': restored},
                indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_missing_image_component_cannot_be_tolerated_as_an_extra_failure(self):
        name = 'ew-packages-component-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13445', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            # Deliberately break an image-supplied component in this disposable fixture.
            docker('exec', name, 'pacman', '-Rdd', '--noconfirm', 'git')
            inventory = command('packages', '--profile', profile)
            self.assertEqual(inventory['state'], 'image-component-failure')
            components = {entry['name']: entry for entry in inventory['imageComponents']}
            self.assertEqual(components['git']['state'], 'missing')
            rejected = invoke(CLI, 'packages', '--profile', profile, '--restore')
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('Supplied image components are missing: git', rejected.stderr)
            (profile / 'component-failure-result.json').write_text(json.dumps({'result': 'passed',
                'component': components['git'], 'restoreExit': rejected.returncode}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_missing_repository_package_and_unknown_source_require_attention(self):
        name = 'ew-packages-manual-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        missing = 'workstation-retired-fixture-' + uuid.uuid4().hex[:10]
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13446', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            install_local_fixture(name, '/config/projects/unregistered-build')
            # A restored inventory can refer to a package no longer in a repository.
            # Keep a real persistent record and let pacman perform the actual lookup.
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'import json,sys; from pathlib import Path; p=Path("/config/.local/state/electivus/packages.json"); '
                   'd=json.loads(p.read_text()); d["extras"].append({"name":sys.argv[1], "version":"1.0-1", '
                   '"origin":"official", "reason":"explicit"}); p.write_text(json.dumps(d))', missing)
            command('stop', '--profile', profile)
            docker('container', 'rm', name)
            command('start', '--profile', profile)
            result = command('packages', '--profile', profile, '--restore')
            (profile / 'manual-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            self.assertEqual(result['state'], 'partial', result)
            reports = {entry['name']: entry for entry in result['packages']}
            self.assertEqual(reports[missing]['state'], 'missing')
            self.assertIn('target not found', reports[missing]['diagnostic'].lower())
            for package in ['workstation-local-example', 'workstation-local-example-debug']:
                self.assertEqual(reports[package]['state'], 'manual-required')
                self.assertIn('Register the persistent build source', reports[package]['diagnostic'])
            self.assertTrue(command('status', '--profile', profile)['healthy'])
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_local_rebuild_failure_keeps_desktop_and_apps_usable_and_can_retry(self):
        name = 'ew-packages-local-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        source = '/config/projects/local-build'
        package = 'workstation-local-example'
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13444', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            install_local_fixture(name, source, dependency=True)
            self.assertEqual(docker('exec', name, package), 'workstation local example')
            registered = command('packages', '--profile', profile, '--register', package, '--source', source)
            extras = {entry['name']: entry for entry in registered['extras']}
            self.assertEqual(extras[package]['origin'], 'foreign')
            self.assertEqual(extras[package]['source']['directory'], source)
            self.assertEqual(extras[package]['source']['kind'], 'local')
            self.assertEqual(extras[package + '-debug']['source'], extras[package]['source'])
            for target in [package, package + '-debug']:
                self.assertEqual(extras[target]['reason'], 'dependency')
            command('stop', '--profile', profile)
            docker('container', 'rm', name)
            command('start', '--profile', profile)
            # Keep the old built archive, then edit and re-checksum its source.
            # Recovery must compile the changed source against this container.
            changed_source = (ROOT / 'tests/fixtures/extra-package/example.c').read_text().replace(
                'workstation local example', 'rebuilt on current Arch')
            write_build_source(name, source, changed_source)
            restored = command('packages', '--profile', profile, '--restore')
            (profile / 'local-restore-attempt.json').write_text(json.dumps(restored, indent=2), encoding='utf-8')
            self.assertEqual(restored['state'], 'completed', restored)
            reports = {entry['name']: entry for entry in restored['packages']}
            self.assertEqual(reports[package]['state'], 'restored')
            self.assertEqual(reports[package]['method'], 'rebuilt')
            self.assertEqual(docker('exec', name, package), 'rebuilt on current Arch')
            installed = {entry['name']: entry for entry in command('packages', '--profile', profile)['extras']}
            for target in [package, package + '-debug']:
                self.assertEqual(installed[target]['reason'], 'dependency')
            command('prepare', '--profile', profile)
            chrome = docker('exec', '--user', 'abc', name, 'google-chrome', '--version')
            write_build_source(name, source, changed_source + '\n#error intentional extra package build failure\n')
            command('stop', '--profile', profile)
            docker('container', 'rm', name)
            command('start', '--profile', profile)
            failed = command('packages', '--profile', profile, '--restore')
            (profile / 'failed-build-report.json').write_text(json.dumps(failed, indent=2), encoding='utf-8')
            self.assertEqual(failed['state'], 'partial', failed)
            failures = {entry['name']: entry for entry in failed['packages']}
            for extra in [package, package + '-debug']:
                self.assertEqual(failures[extra]['state'], 'build-failed')
                self.assertIn('intentional extra package build failure', failures[extra]['diagnostic'])
            self.assertEqual(command('packages', '--profile', profile)['lastRestore'], failed)
            self.assertTrue(command('status', '--profile', profile)['healthy'])
            self.assertEqual(docker('exec', '--user', 'abc', name, 'google-chrome', '--version'), chrome)
            rendered = docker('exec', '--user', 'abc', name, 'timeout', '30', 'google-chrome', '--headless',
                              '--disable-gpu', '--user-data-dir=/tmp/package-browser-probe', '--dump-dom',
                              'data:text/html,<h1>Browser usable after extra failure</h1>')
            self.assertIn('<h1>Browser usable after extra failure</h1>', rendered)
            write_build_source(name, source, changed_source)
            retried = command('packages', '--profile', profile, '--restore')
            self.assertEqual(retried['state'], 'completed', retried)
            self.assertEqual(docker('exec', name, package), 'rebuilt on current Arch')
            (profile / 'local-package-result.json').write_text(json.dumps({'result': 'passed',
                'registered': extras[package], 'restore': restored, 'oldArchiveReused': False,
                'failedBuild': failed, 'retry': retried, 'chromeAfterFailure': chrome,
                'chromeRenderedAfterFailure': True}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_pacman_transactions_and_assisted_recovery(self):
        name = 'ew-packages-pacman-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13443', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            docker('exec', name, 'workstation-network', 'exec', '--', 'pacman', '-Syu', '--needed',
                   '--disable-download-timeout', '--noprogressbar', '--noconfirm', 'figlet')
            installed = command('packages', '--profile', profile)
            extras = {entry['name']: entry for entry in installed['extras']}
            self.assertIn('figlet', extras)
            self.assertEqual(extras['figlet']['origin'], 'official')
            self.assertEqual(extras['figlet']['reason'], 'explicit')
            self.assertEqual(extras['figlet']['state'], 'installed')
            command('stop', '--profile', profile)
            docker('container', 'rm', name)
            command('start', '--profile', profile)
            recreated = command('packages', '--profile', profile)
            extras = {entry['name']: entry for entry in recreated['extras']}
            self.assertEqual(extras['figlet']['state'], 'missing')
            self.assertEqual(recreated['state'], 'partial')
            restored = command('packages', '--profile', profile, '--restore')
            self.assertEqual(restored['state'], 'completed')
            reports = {entry['name']: entry for entry in restored['packages']}
            self.assertEqual(reports['figlet']['state'], 'restored')
            docker('exec', name, 'figlet', 'restored')
            docker('exec', name, 'pacman', '-R', '--noconfirm', 'figlet')
            removed = command('packages', '--profile', profile)
            self.assertNotIn('figlet', {entry['name'] for entry in removed['extras']})
            self.assertEqual(removed['state'], 'ready')
            (profile / 'pacman-result.json').write_text(json.dumps({'result': 'passed',
                'installed': installed, 'recreated': recreated, 'restored': restored,
                'removed': removed}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)

    def test_inventory_distinguishes_image_components(self):
        name = 'ew-packages-inventory-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13440', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            inventory = command('packages', '--profile', profile)
            self.assertEqual(inventory['schema'], 1)
            self.assertEqual(inventory['extras'], [])
            names = {package['name'] for package in inventory['imageComponents']}
            self.assertTrue({'git', 'zsh', 'pacman'}.issubset(names))
            variant = json.loads(docker('image', 'inspect', IMAGE))[0]['Config']['Labels']['io.electivus.workstation.variant']
            if variant == 'salesforce':
                self.assertTrue({'nodejs-lts-krypton', 'npm', 'jdk21-openjdk'}.issubset(names))
            self.assertEqual(inventory['state'], 'ready')
            linux = json.loads(docker('exec', name, 'workstation-packages', 'status'))
            self.assertEqual(linux, inventory)
            (profile / 'inventory-result.json').write_text(json.dumps({'result': 'passed',
                'imageComponents': len(names), 'extras': inventory['extras']}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
