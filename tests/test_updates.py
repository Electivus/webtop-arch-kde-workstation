"""Explicit maintenance through the delivered commands and real applications."""
import json
import os
import signal
from pathlib import Path
import subprocess
import time
import unittest
import uuid

from test_commands import ROOT, CLI, command, docker, invoke
from test_backups import discard_backup_archives
from test_packages import configure_test_network

BASE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t09-t10')
SALESFORCE = os.environ.get('WORKSTATION_SALESFORCE_TEST_IMAGE', 'electivus/webtop-arch-kde-salesforce:t09-t10')


def update_command(action, profile, *arguments):
    result = invoke(CLI, action, '--profile', profile, *arguments, timeout=2100)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def chrome_page(name):
    return docker('exec', '--user', 'abc', name, 'timeout', '30', 'google-chrome', '--headless',
                  '--disable-gpu', '--user-data-dir=/tmp/update-browser-probe', '--dump-dom',
                  'file:///config/projects/maintenance.html')


class UpdateAcceptance(unittest.TestCase):
    def test_status_distinguishes_a_killed_host_command_from_an_active_update(self):
        name = 'ew-update-interrupted-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        operation = None
        reports = {}
        try:
            command('install', '--profile', profile, '--name', name, '--image', BASE,
                    '--port', '13458', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            for action in ('update-apps', 'update-image'):
                self.assertEqual(command(action, '--profile', profile, '--status')['state'], 'not-started')
            for action in ('update-apps', 'update-image'):
                with self.subTest(action=action):
                    command('start', '--profile', profile)
                    docker('exec', '--user', 'abc', name, 'python3', '-c',
                           'from pathlib import Path; Path("/config/projects/interrupted-copy.bin").open("wb").truncate(512*1024*1024)')
                    executable = CLI.with_suffix('.exe') if os.name == 'nt' else CLI
                    arguments = ['--image', BASE, '--pull=false'] if action == 'update-image' else []
                    operation = subprocess.Popen([str(executable), action, '--profile', str(profile), *arguments],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                    progress = operation.stderr.readline()
                    self.assertIn('Stopping the workstation', progress)
                    if os.name != 'nt':
                        os.kill(operation.pid, signal.SIGSTOP)
                        _, state = os.waitpid(operation.pid, os.WUNTRACED)
                        self.assertTrue(os.WIFSTOPPED(state))
                    active = command(action, '--profile', profile, '--status')
                    self.assertEqual(active['state'], 'running')
                    self.assertEqual(active['step'], 'backup')
                    for previous in reports:
                        self.assertEqual(command(previous, '--profile', profile, '--status')['state'], 'interrupted',
                                         'A different active operation must not revive an abandoned update')
                    self.assertIsNone(operation.poll(), 'The interruption must terminate a live command')
                    operation.kill()
                    operation.communicate(timeout=30)
                    # Settle a Docker stop request that can outlive its host
                    # command before checking the report and explicitly restarting.
                    command('stop', '--profile', profile)
                    interrupted = command(action, '--profile', profile, '--status')
                    self.assertEqual(interrupted['state'], 'interrupted')
                    self.assertEqual(interrupted['step'], active['step'])
                    self.assertEqual(interrupted['startedAt'], active['startedAt'])
                    self.assertNotIn('completedAt', interrupted)
                    reports[action] = interrupted
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', name, 'stat', '-c', '%s', '/config/projects/interrupted-copy.bin'),
                             str(512*1024*1024))
            (profile / 'host-interruption-result.json').write_text(json.dumps({'result': 'passed' if len(reports) == 2 else 'failed',
                'attempts': reports, 'explicitRestart': 'healthy'}, indent=2), encoding='utf-8')
        finally:
            if operation is not None and operation.poll() is None:
                operation.kill()
                operation.communicate(timeout=30)
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_extension_install_failure_is_reported_with_a_recoverable_backup(self):
        name = 'ew-update-extension-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        older = 'salesforce.salesforcedx-vscode-visualforce@67.14.0'
        try:
            cpus = str(min(4, int(docker('info', '--format', '{{.NCPU}}'))))
            command('install', '--profile', profile, '--name', name, '--image', SALESFORCE,
                    '--port', '13457', '--memory', '6144', '--cpus', cpus, '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'code', '--install-extension', older, '--force')
            prepared = command('prepare', '--profile', profile)
            self.assertIn(older, prepared['apps']['extensions']['code']['versions'])
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Project before extension installation failure</h1>")')
            docker('exec', name, 'chmod', '555', '/config/.vscode/extensions')
            attempted = invoke(CLI, 'update-apps', '--profile', profile, timeout=2100)
            (profile / 'extension-install-attempt.log').write_text(attempted.stdout + attempted.stderr, encoding='utf-8')
            self.assertEqual(docker('exec', name, 'stat', '-c', '%a', '/config/.vscode/extensions'), '555')
            failed = command('update-apps', '--profile', profile, '--status')
            (profile / 'extension-install-attempt.json').write_text(json.dumps(failed, indent=2), encoding='utf-8')
            self.assertNotEqual(attempted.returncode, 0, attempted.stdout + attempted.stderr)
            self.assertEqual(failed['state'], 'failed', failed)
            self.assertEqual(failed['applications']['app'], 'code extensions')
            self.assertEqual(failed['backup']['state'], 'completed')
            self.assertIn(older, docker('exec', '--user', 'abc', name, 'code',
                                       '--list-extensions', '--show-versions').splitlines())
            self.assertTrue(command('status', '--profile', profile)['healthy'])
            self.assertIn('Project before extension installation failure', chrome_page(name))
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text("changed after failure")')
            restored = command('restore', '--profile', profile, '--backup', failed['backup']['directory'])
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Project before extension installation failure', chrome_page(name))
            self.assertEqual(command('update-apps', '--profile', profile, '--status'), failed)
            (profile / 'extension-failure-update-result.json').write_text(json.dumps({'result': 'passed',
                'update': failed, 'restored': restored}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def exercise_salesforce_project(self, name, profile, stage):
        workspace = '/config/projects/maintenance-sf'
        docker('cp', str(ROOT / 'tests/editor_probe'), name + ':/config/editor_probe')
        for editor in ['code', 'code-insiders']:
            docker('cp', str(ROOT / 'tests/salesforce_sample') + '/.', name + ':' + workspace)
            docker('exec', name, 'chown', '-R', '1000:1000', '/config/editor_probe', workspace)
            receipt = '/config/' + stage + '-' + editor + '-services.json'
            exercised = subprocess.run(['docker', 'exec', '--user', 'abc', '--env',
                'ELECTIVUS_TEST_RESULT=' + receipt, name, 'timeout', '300', editor,
                '--wait', '--new-window', '--verbose', '--disable-workspace-trust', '--skip-welcome',
                '--skip-release-notes', '--extensionDevelopmentPath=/config/editor_probe',
                '--extensionTestsPath=/config/editor_probe/index.js', workspace],
                capture_output=True, text=True, encoding='utf-8', timeout=330)
            (profile / (stage + '-' + editor + '-services.log')).write_text(
                exercised.stdout + exercised.stderr, encoding='utf-8')
            result = json.loads(docker('exec', name, 'cat', receipt))
            self.assertEqual(exercised.returncode, 0, exercised.stdout + exercised.stderr)
            self.assertEqual(result['result'], 'passed', result)
            (profile / (stage + '-' + editor + '-services.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        kde = ['exec', '--user', 'abc', name, 'env', 'XDG_CURRENT_DESKTOP=KDE', 'KDE_SESSION_VERSION=6']
        self.assertEqual(docker(*kde, 'xdg-mime', 'query', 'default', 'application/x-code-workspace'), 'code-insiders.desktop')
        self.assertIn('Salesforce maintenance project', chrome_page(name))

    def test_salesforce_cli_and_extensions_update_and_recover_with_the_project(self):
        name = 'ew-update-sf-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        fixture = name + ':fixture'
        member = 'salesforce.salesforcedx-vscode-visualforce'
        older_extension = member + '@67.14.0'
        try:
            profile.mkdir(parents=True)
            built = subprocess.run(['docker', 'build', '--build-arg', 'BASE_IMAGE=' + SALESFORCE,
                '--tag', fixture, str(ROOT / 'tests/fixtures/application-updates')],
                capture_output=True, text=True, encoding='utf-8', timeout=180)
            (profile / 'fixture-build.log').write_text(built.stdout + built.stderr, encoding='utf-8')
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            cpus = str(min(4, int(docker('info', '--format', '{{.NCPU}}'))))
            command('install', '--profile', profile, '--name', name, '--image', fixture,
                    '--port', '13456', '--memory', '6144', '--cpus', cpus, '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            self.assertEqual(prepared['apps']['salesforce-cli']['version'], '2.149.1')
            for editor in ['code', 'code-insiders']:
                docker('exec', '--user', 'abc', name, editor, '--install-extension', older_extension, '--force')
                self.assertIn(older_extension, docker('exec', '--user', 'abc', name, editor,
                                                     '--list-extensions', '--show-versions').splitlines())
            # Record the actual older release through ordinary preparation,
            # which must leave installed versions alone before the update.
            prepared = command('prepare', '--profile', profile)
            for editor in ['code', 'code-insiders']:
                self.assertIn(older_extension, prepared['apps']['extensions'][editor]['versions'])
            generated = json.loads(docker('exec', '--user', 'abc', name, 'sf', 'project', 'generate',
                '--name', 'maintenance-sf', '--output-dir', '/config/projects', '--json'))
            self.assertEqual(generated['status'], 0, generated)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Salesforce maintenance project</h1>"); '
                   'Path("/config/projects/maintenance-sf/personal.txt").write_text("preserve my work")')
            updated = update_command('update-apps', profile)
            (profile / 'salesforce-update-attempt.json').write_text(json.dumps(updated, indent=2), encoding='utf-8')
            self.assertEqual(updated['state'], 'completed', updated)
            unchanged = []
            if updated['applications']['apps']['salesforce-cli']['version'] == '2.149.1':
                unchanged.append('Salesforce CLI')
            for editor in ['code', 'code-insiders']:
                actual = docker('exec', '--user', 'abc', name, editor, '--list-extensions', '--show-versions').splitlines()
                self.assertEqual(sorted(actual), updated['applications']['apps']['extensions'][editor]['versions'])
                if older_extension in actual:
                    unchanged.append(editor + ' Visualforce')
            self.assertEqual(unchanged, [], 'Explicit update left older installed releases unchanged')
            self.assertEqual(command('status', '--profile', profile)['imageId'], before['imageId'])
            self.assertEqual(docker('exec', '--user', 'abc', name, 'sf', '--version'),
                             updated['applications']['apps']['salesforce-cli']['actualVersion'])
            self.exercise_salesforce_project(name, profile, 'updated')
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], updated['applications']['apps'])
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance-sf/personal.txt").write_text("changed after update")')
            restored = command('restore', '--profile', profile, '--backup', updated['backup']['directory'])
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/maintenance-sf/personal.txt'),
                             'preserve my work')
            self.exercise_salesforce_project(name, profile, 'restored')
            (profile / 'salesforce-update-result.json').write_text(json.dumps({'result': 'passed',
                'update': updated, 'restored': restored, 'bothEditorsAfterUpdateAndRestore': True}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            subprocess.run(['docker', 'image', 'rm', fixture], capture_output=True)

    def test_application_backup_failures_preserve_the_running_installation(self):
        name = 'ew-update-backup-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', BASE,
                    '--port', '13455', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            original_profile = (profile / 'profile.json').read_bytes()
            blocked = profile / 'not-a-backup-directory'
            blocked.write_text('existing file must survive', encoding='utf-8')
            results = []
            for phase in ['before-stop', 'after-stop']:
                started_at = json.loads(docker('inspect', name))[0]['State']['StartedAt']
                arguments = ['--backup-directory', blocked] if phase == 'before-stop' else []
                if phase == 'after-stop':
                    certificates = profile / 'certificates'
                    certificates.mkdir(exist_ok=True)
                    (certificates / 'broken.crt').write_text('damaged archived certificate', encoding='utf-8')
                    pending = profile / 'pending-network.json'
                    settings = {'proxy': 'http://127.0.0.1:9'}
                    if os.environ.get('WORKSTATION_TEST_CA_FILE'):
                        settings['caFiles'] = [os.environ['WORKSTATION_TEST_CA_FILE']]
                    pending.write_text(json.dumps(settings), encoding='utf-8')
                    command('network', '--profile', profile, '--network-config', pending)
                attempted = invoke(CLI, 'update-apps', '--profile', profile, *arguments, timeout=2100)
                self.assertNotEqual(attempted.returncode, 0)
                failed = command('update-apps', '--profile', profile, '--status')
                self.assertEqual(failed['state'], 'failed')
                self.assertEqual(failed['step'], 'backup')
                self.assertNotIn('applications', failed)
                deadline = time.monotonic() + 90
                after = command('status', '--profile', profile)
                while not after['healthy'] and time.monotonic() < deadline:
                    time.sleep(1)
                    after = command('status', '--profile', profile)
                self.assertTrue(after['healthy'], after)
                self.assertEqual(after['containerId'], before['containerId'])
                self.assertEqual(after['imageId'], before['imageId'])
                self.assertEqual((profile / 'profile.json').read_bytes(), original_profile)
                self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
                current_started = json.loads(docker('inspect', name))[0]['State']['StartedAt']
                if phase == 'before-stop':
                    self.assertEqual(current_started, started_at)
                else:
                    self.assertNotEqual(current_started, started_at)
                    self.assertIn('invalid local certificate archive', failed['error'])
                    # The existing runtime still reaches the vendor; the pending
                    # refusing proxy must not be applied while undoing a failed backup.
                    docker('exec', '--user', 'abc', name, 'workstation-network', 'exec', '--', 'curl',
                           '--fail', '--silent', '--head', '--max-time', '30',
                           'https://dl.google.com/linux/chrome/deb/dists/stable/Release')
                results.append({'phase': phase, 'report': failed, 'containerStartedAt': current_started})
            self.assertEqual(blocked.read_text(), 'existing file must survive')
            self.assertEqual(command('backup', '--profile', profile, '--list')['backups'], [])
            (profile / 'backup-failure-update-result.json').write_text(json.dumps({'result': 'passed',
                'failures': results}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_failed_application_download_keeps_its_backup_and_startup_does_not_retry_update(self):
        name = 'ew-update-download-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', BASE,
                    '--port', '13454', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Project protected before failed update</h1>")')
            settings = {'proxy': 'http://127.0.0.1:9'}
            if os.environ.get('WORKSTATION_TEST_CA_FILE'):
                settings['caFiles'] = [os.environ['WORKSTATION_TEST_CA_FILE']]
            network = profile / 'unreachable-network.json'
            network.write_text(json.dumps(settings), encoding='utf-8')
            command('network', '--profile', profile, '--network-config', network)
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            attempted = invoke(CLI, 'update-apps', '--profile', profile, timeout=2100)
            self.assertNotEqual(attempted.returncode, 0)
            failed = command('update-apps', '--profile', profile, '--status')
            self.assertEqual(failed['state'], 'failed', failed)
            self.assertEqual(failed['step'], 'applications')
            self.assertEqual(failed['applications']['state'], 'failed')
            self.assertIn('Connection refused', failed['applications']['error'])
            self.assertEqual(failed['backup']['state'], 'completed')
            self.assertEqual(failed['previous']['imageId'], before['imageId'])
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            # The proxy still refuses downloads. Normal preparation must reuse
            # the working artifacts, leaving the explicit failed update visible.
            reused = command('prepare', '--profile', profile)
            self.assertEqual(reused['state'], 'completed')
            self.assertEqual(reused['apps'], prepared['apps'])
            self.assertEqual(command('update-apps', '--profile', profile, '--status'), failed)
            self.assertIn('Project protected before failed update', chrome_page(name))
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text("changed after failure")')
            recovered = command('restore', '--profile', profile, '--backup', failed['backup']['directory'])
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Project protected before failed update', chrome_page(name))
            (profile / 'failed-update-result.json').write_text(json.dumps({'result': 'passed',
                'attemptExit': attempted.returncode, 'update': failed, 'restore': recovered}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_application_update_backups_and_preserves_the_image(self):
        name = 'ew-update-apps-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', BASE,
                    '--port', '13451', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Personal project before update</h1>")')
            updated = update_command('update-apps', profile)
            self.assertEqual(updated['state'], 'completed', updated)
            self.assertEqual(updated['previous']['imageId'], before['imageId'])
            self.assertEqual(updated['backup']['state'], 'completed')
            after = command('status', '--profile', profile)
            self.assertEqual(after['imageId'], before['imageId'])
            self.assertEqual(after['version'], before['version'])
            self.assertTrue(after['healthy'])
            actual = docker('exec', '--user', 'abc', name, 'google-chrome', '--version')
            self.assertEqual(updated['applications']['apps']['chrome']['actualVersion'], actual)
            self.assertTrue(updated['applications']['apps']['chrome']['source'].startswith('https://dl.google.com/'))
            self.assertIn('Personal project before update', chrome_page(name))
            listed = command('backup', '--profile', profile, '--list')['backups']
            self.assertIn(updated['backup']['id'], [entry['id'] for entry in listed])
            self.assertEqual(command('update-apps', '--profile', profile, '--status'), updated)
            command('stop', '--profile', profile)
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], updated['applications']['apps'])
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text("changed after update")')
            recovered = command('restore', '--profile', profile, '--backup', updated['backup']['directory'])
            command('start', '--profile', profile)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Personal project before update', chrome_page(name))
            (profile / 'application-update-result.json').write_text(json.dumps({
                'result': 'passed', 'update': updated, 'restore': recovered,
                'browserAfterUpdateAndRestore': True}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')


if __name__ == '__main__':
    unittest.main(verbosity=2)
