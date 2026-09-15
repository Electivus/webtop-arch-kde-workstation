"""Personal backup and recovery through the delivered Windows commands."""
import json
import hashlib
import base64
import io
import os
import signal
from pathlib import Path
import subprocess
import tarfile
import unittest
import uuid

from test_commands import ROOT, CLI, command, docker, invoke

IMAGE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t07')
SALESFORCE = os.environ.get('WORKSTATION_SALESFORCE_TEST_IMAGE', 'electivus/webtop-arch-kde-salesforce:t07')


def discard_backup_archives(directory):
    directory = directory.resolve()
    if not directory.is_relative_to((ROOT / '.local').resolve()) or directory == (ROOT / '.local').resolve():
        raise RuntimeError('test backup directory is outside the owned test workspace')
    for archive in directory.glob('*/home.tar'):
        if not archive.resolve().is_relative_to(directory):
            raise RuntimeError('test archive resolves outside its directory')
        archive.unlink()


def write_manifest(directory, manifest):
    data = json.dumps(manifest, indent=2).encode('utf-8')
    (directory / 'manifest.json').write_bytes(data)
    (directory / 'manifest.sha256').write_text(hashlib.sha256(data).hexdigest() + '\n', encoding='ascii')


class BackupAcceptance(unittest.TestCase):
    def test_archive_replaced_after_validation_cannot_be_committed(self):
        name = 'ew-backup-race-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        operation = None
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13441', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/live.txt").write_text("original data")')
            saved = command('backup', '--profile', profile)
            command('start', '--profile', profile)
            original_profile = (profile / 'profile.json').read_bytes()
            changed = io.BytesIO()
            with tarfile.open(fileobj=changed, mode='w') as archive:
                payload = b'changed after validation'
                member = tarfile.TarInfo('projects/live.txt')
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            executable = CLI.with_suffix('.exe') if os.name == 'nt' else CLI
            operation = subprocess.Popen([str(executable), 'restore', '--profile', str(profile),
                                          '--backup', saved['directory']],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            progress = operation.stderr.readline()
            self.assertIn('Stopping the workstation', progress)
            # This public notice follows the initial validation and precedes
            # Docker's graceful stop and creation of the extraction volume.
            (Path(saved['directory']) / 'home.tar').write_bytes(changed.getvalue())
            output, diagnostic = operation.communicate(timeout=180)
            self.assertNotEqual(operation.returncode, 0, output)
            self.assertIn('changed during restore', diagnostic.lower())
            self.assertEqual((profile / 'profile.json').read_bytes(), original_profile)
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/live.txt'), 'original data')
            (profile / 'archive-race-result.json').write_text(json.dumps({'result': 'passed',
                'replacement': 'valid tar after initial validation', 'profileAndOriginalVolume': 'preserved'},
                indent=2), encoding='utf-8')
        finally:
            if operation is not None and operation.poll() is None:
                operation.communicate(timeout=180)
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_manifest_corruption_is_rejected_even_when_fields_remain_valid(self):
        name = 'ew-backup-metadata-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13439', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            network_input = profile / 'network-input.json'
            network_input.write_text(json.dumps({'proxy': 'http://127.0.0.1:9'}), encoding='utf-8')
            command('network', '--profile', profile, '--network-config', network_input)
            saved = command('backup', '--profile', profile)
            command('start', '--profile', profile)
            profile_before = (profile / 'profile.json').read_bytes()
            network_before = (profile / 'network.json').read_bytes()
            manifest_file = Path(saved['directory']) / 'manifest.json'
            manifest_before = manifest_file.read_bytes()
            for field in ['port', 'network']:
                damaged = json.loads(manifest_before)
                if field == 'port':
                    damaged['profile']['port'] = 13440
                else:
                    payload = json.loads(base64.b64decode(damaged['hostFiles']['network.json']))
                    payload['proxy'] = 'http://127.0.0.1:8'
                    damaged['hostFiles']['network.json'] = base64.b64encode(json.dumps(payload).encode()).decode()
                manifest_file.write_text(json.dumps(damaged), encoding='utf-8')
                try:
                    rejected = invoke(CLI, 'restore', '--profile', profile, '--backup', saved['directory'])
                    self.assertNotEqual(rejected.returncode, 0, field)
                    self.assertIn('manifest checksum', rejected.stderr.lower())
                    self.assertEqual((profile / 'profile.json').read_bytes(), profile_before)
                    self.assertEqual((profile / 'network.json').read_bytes(), network_before)
                    self.assertEqual(command('status', '--profile', profile)['state'], 'running')
                    listed = command('backup', '--profile', profile, '--list')
                    self.assertEqual(listed['backups'], [])
                    self.assertIn(saved['id'], listed['incomplete'])
                finally:
                    manifest_file.write_bytes(manifest_before)
            checksum_file = Path(saved['directory']) / 'manifest.sha256'
            checksum_before = checksum_file.read_bytes()
            checksum_file.unlink()
            try:
                rejected = invoke(CLI, 'restore', '--profile', profile, '--backup', saved['directory'])
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn('incomplete backup manifest checksum', rejected.stderr.lower())
                self.assertEqual(command('status', '--profile', profile)['state'], 'running')
            finally:
                checksum_file.write_bytes(checksum_before)
            self.assertEqual(len(command('backup', '--profile', profile, '--list')['backups']), 1)
            (profile / 'metadata-result.json').write_text(json.dumps({'result': 'passed',
                'validPortChange': 'rejected', 'validNetworkChange': 'rejected',
                'runningSessionAndHostState': 'preserved'}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_incomplete_backup_profile_is_rejected_before_changing_live_data(self):
        name = 'ew-backup-profile-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13438', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/current.txt").write_text("keep live data")')
            saved = command('backup', '--profile', profile)
            command('start', '--profile', profile)
            profile_before = (profile / 'profile.json').read_bytes()
            manifest_file = Path(saved['directory']) / 'manifest.json'
            manifest_before = manifest_file.read_bytes()
            checksum_file = Path(saved['directory']) / 'manifest.sha256'
            checksum_before = checksum_file.read_bytes()
            manifest = json.loads(manifest_before)
            cases = [('missing', None), ('null', None), ('empty', {})]
            for field, value in {'schema': 2, 'installationId': '', 'name': 'invalid/name', 'image': '',
                                 'port': 0, 'memoryMiB': 0, 'cpus': 0, 'homeVolume': 'unrelated',
                                 'dockerContext': ''}.items():
                cases.append((field, {**manifest['profile'], field: value}))
            for label, damaged_profile in cases:
                damaged = {**manifest, 'profile': damaged_profile}
                if label == 'missing':
                    del damaged['profile']
                write_manifest(manifest_file.parent, damaged)
                try:
                    rejected = invoke(CLI, 'restore', '--profile', profile, '--backup', saved['directory'])
                    self.assertNotEqual(rejected.returncode, 0, label)
                    self.assertIn('backup profile', rejected.stderr.lower(), label)
                    self.assertEqual((profile / 'profile.json').read_bytes(), profile_before, label)
                    self.assertEqual(command('status', '--profile', profile)['state'], 'running', label)
                    self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/current.txt'),
                                     'keep live data', label)
                finally:
                    manifest_file.write_bytes(manifest_before)
                    checksum_file.write_bytes(checksum_before)
            self.assertEqual([entry['id'] for entry in command('backup', '--profile', profile, '--list')['backups']],
                             [saved['id']])
            (profile / 'invalid-profile-result.json').write_text(json.dumps({'result': 'passed',
                'rejectedProfiles': [label for label, _ in cases], 'liveState': 'preserved without interruption'},
                indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_corrupted_copy_cannot_displace_a_valid_backup(self):
        name = 'ew-backup-corrupt-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13437', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/retained.txt").write_text("first valid copy")')
            first = command('backup', '--profile', profile)
            corrupted = command('backup', '--profile', profile)
            archive = Path(corrupted['directory']) / 'home.tar'
            with archive.open('r+b') as stream:
                original = stream.read(1)
                stream.seek(0)
                stream.write(bytes([original[0] ^ 1]))
            rejected = invoke(CLI, 'restore', '--profile', profile, '--backup', corrupted['directory'])
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('checksum', rejected.stderr.lower())
            newest = command('backup', '--profile', profile)
            self.assertTrue((Path(first['directory']) / 'home.tar').is_file(),
                            'same-size corruption must not cause a valid older copy to be deleted')
            listed = command('backup', '--profile', profile, '--list')
            self.assertEqual([entry['id'] for entry in listed['backups']], [newest['id'], first['id']])
            self.assertIn(corrupted['id'], listed['incomplete'])
            restored = command('restore', '--profile', profile, '--backup', first['directory'])
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/retained.txt'),
                             'first valid copy')
            (profile / 'corruption-result.json').write_text(json.dumps({'result': 'passed',
                'corruptedCopy': corrupted['id'], 'retained': listed, 'restore': restored}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_project_volume_writers_must_stop_before_backup_or_restore(self):
        name = 'ew-backup-writers-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        project = name + '-project'
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13436', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/consistent.txt").write_text("saved project")')
            mount = 'type=volume,src=' + name + '-home,dst=/config,volume-nocopy'
            docker('run', '--detach', '--name', project, '--network', 'none', '--mount', mount + ',readonly',
                   '--entrypoint', '/bin/sleep', IMAGE, 'infinity')
            saved = command('backup', '--profile', profile)
            self.assertEqual(docker('inspect', '--format', '{{.State.Running}}', project), 'true')
            docker('container', 'rm', '--force', '--volumes', project)
            command('start', '--profile', profile)
            docker('run', '--detach', '--name', project, '--network', 'none', '--mount', mount,
                   '--entrypoint', '/bin/sleep', IMAGE, 'infinity')
            for operation in [('backup',), ('restore', '--backup', saved['directory'])]:
                rejected = invoke(CLI, *operation, '--profile', profile)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(project, rejected.stderr)
                self.assertEqual(command('status', '--profile', profile)['state'], 'running')
                self.assertEqual(docker('inspect', '--format', '{{.State.Running}}', project), 'true')
            docker('stop', '--time', '1', project)
            recovered = command('restore', '--profile', profile, '--backup', saved['directory'])
            self.assertEqual(recovered['retainedPreviousVolume'], name + '-home')
            docker('volume', 'inspect', name + '-home')
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/consistent.txt'), 'saved project')
            (profile / 'volume-writers-result.json').write_text(json.dumps({'result': 'passed',
                'readOnlyObserver': 'preserved while backup completed', 'activeWriter': 'both operations rejected',
                'stoppedAttachment': 'previous volume retained', 'restore': recovered}, indent=2), encoding='utf-8')
        finally:
            for container in [project, name]:
                subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', container], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_salesforce_applications_and_preferences_restore_offline(self):
        name = 'ew-backup-sf-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        try:
            cpus = str(min(4, int(docker('info', '--format', '{{.NCPU}}'))))
            command('install', '--profile', profile, '--name', name, '--image', SALESFORCE,
                    '--port', '13434', '--memory', '6144', '--cpus', cpus, '--no-shortcut')
            command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            self.assertEqual(prepared['state'], 'completed')
            programs = ['google-chrome', 'code', 'code-insiders', 'sf']
            versions = {program: docker('exec', '--user', 'abc', name, program, '--version') for program in programs}
            extensions = {editor: sorted(docker('exec', '--user', 'abc', name, editor, '--list-extensions', '--show-versions').splitlines())
                          for editor in ['code', 'code-insiders']}
            generated = json.loads(docker('exec', '--user', 'abc', name, 'sf', 'project', 'generate',
                                         '--name', 'recovery', '--output-dir', '/config/projects', '--json'))
            self.assertEqual(generated['status'], 0)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; p=Path("/config/projects/recovery/force-app/main/default/classes/BackupProbe.cls"); '
                   'p.parent.mkdir(parents=True,exist_ok=True); p.write_text("public class BackupProbe {}")')
            configured = json.loads(docker('exec', '--user', 'abc', name, 'sf', 'config', 'set',
                                          'org-instance-url=https://test.salesforce.com', '--global', '--json'))
            self.assertEqual(configured['status'], 0)
            # A refusing local proxy prevents startup from repairing missing applications by downloading them.
            network_input = profile / 'offline-input.json'
            network_input.write_text(json.dumps({'proxy': 'http://127.0.0.1:9'}), encoding='utf-8')
            command('network', '--profile', profile, '--network-config', network_input)
            saved = command('backup', '--profile', profile)
            command('start', '--profile', profile)
            command('network', '--profile', profile, '--clear')
            docker('exec', '--user', 'abc', name, 'sf', 'config', 'set',
                   'org-instance-url=https://login.salesforce.com', '--global', '--json')
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/recovery/force-app/main/default/classes/BackupProbe.cls").write_text("changed")')
            recovered = command('restore', '--profile', profile, '--backup', saved['directory'])
            self.assertTrue(command('network', '--profile', profile)['proxyConfigured'])
            command('start', '--profile', profile)
            for program in programs:
                self.assertEqual(docker('exec', '--user', 'abc', name, program, '--version'), versions[program])
            for editor in extensions:
                self.assertEqual(sorted(docker('exec', '--user', 'abc', name, editor, '--list-extensions', '--show-versions').splitlines()),
                                 extensions[editor])
            preference = json.loads(docker('exec', '--user', 'abc', name, 'sf', 'config', 'get', 'org-instance-url', '--json'))
            self.assertEqual(preference['status'], 0)
            self.assertEqual(preference['result'][0]['value'], 'https://test.salesforce.com')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat',
                                   '/config/projects/recovery/force-app/main/default/classes/BackupProbe.cls'), 'public class BackupProbe {}')
            self.assertEqual(command('prepare', '--profile', profile, '--status')['apps'], prepared['apps'])
            (profile / 'salesforce-backup-result.json').write_text(json.dumps({'result': 'passed',
                'versions': versions, 'extensions': extensions, 'orgInstanceURL': 'https://test.salesforce.com',
                'restoredNetworkProfile': True, 'downloadsUnavailableAfterRestore': True,
                'backup': saved, 'restore': recovered}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_start_during_backup_is_rejected_without_interrupting_the_copy(self):
        name = 'ew-backup-busy-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        operation = None
        paused = False
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13435', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/large-copy.bin").open("wb").truncate(512*1024*1024)')
            executable = CLI.with_suffix('.exe') if os.name == 'nt' else CLI
            operation = subprocess.Popen([str(executable), 'backup', '--profile', str(profile)],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            progress = operation.stderr.readline()
            self.assertIn('Stopping the workstation', progress)
            if os.name != 'nt':
                # Hold the actual public command at its interruption notice on fast CI disks.
                os.kill(operation.pid, signal.SIGSTOP)
                _, state = os.waitpid(operation.pid, os.WUNTRACED)
                self.assertTrue(os.WIFSTOPPED(state))
                paused = True
            try:
                competing = invoke(CLI, 'start', '--profile', profile, timeout=30)
            finally:
                if paused:
                    os.kill(operation.pid, signal.SIGCONT)
                    paused = False
                output, diagnostic = operation.communicate(timeout=180)
            self.assertNotEqual(competing.returncode, 0)
            self.assertIn('another workstation operation', competing.stderr.lower())
            self.assertEqual(operation.returncode, 0, diagnostic)
            self.assertEqual(json.loads(output)['state'], 'completed')
            self.assertEqual(command('status', '--profile', profile)['state'], 'stopped')
            (profile / 'concurrent-operation-result.json').write_text(json.dumps({'result': 'passed',
                'concurrentStart': 'rejected', 'backup': 'completed'}, indent=2), encoding='utf-8')
        finally:
            if operation is not None and operation.poll() is None:
                if paused:
                    os.kill(operation.pid, signal.SIGCONT)
                operation.communicate(timeout=180)
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_low_space_and_failed_restore_preserve_valid_copies(self):
        name = 'ew-backup-failure-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        helper = name + '-limited'
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13433', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/important.txt").write_text("keep current data"); '
                   'Path("/config/projects/large-data.bin").write_bytes(b"x" * (8*1024*1024))')
            copies = [command('backup', '--profile', profile), command('backup', '--profile', profile)]
            command('start', '--profile', profile)
            capacity = sum(p.stat().st_size for copy in copies for p in Path(copy['directory']).iterdir() if p.is_file()) + 1024*1024
            docker('create', '--name', helper, '--tmpfs', '/limited:size=' + str(capacity),
                   '--mount', 'type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock',
                   '--entrypoint', '/bin/sleep', IMAGE, 'infinity')
            docker('start', helper)
            docker('exec', helper, 'mkdir', '-p', '/tmp/profile')
            docker('cp', str(profile / 'profile.json'), helper + ':/tmp/profile/profile.json')
            docker('cp', str(ROOT / '.local/cli/workstation'), helper + ':/tmp/workstation')
            docker('exec', helper, 'chmod', '755', '/tmp/workstation')
            context = json.loads((profile / 'profile.json').read_text())['dockerContext']
            if context != 'default':
                docker('exec', helper, 'docker', 'context', 'create', context, '--docker', 'host=unix:///var/run/docker.sock')
            for copy in copies:
                # Stage uploads outside tmpfs, then move them using the container's
                # mount namespace so the limited filesystem actually holds the copies.
                docker('cp', copy['directory'], helper + ':/tmp/')
                docker('exec', helper, 'mv', '--', '/tmp/' + copy['id'], '/limited/' + copy['id'])
                docker('exec', helper, 'test', '-f', '/limited/' + copy['id'] + '/home.tar')
            failed = subprocess.run(['docker', 'exec', helper, '/tmp/workstation', 'backup',
                '--profile', '/tmp/profile', '--backup-directory', '/limited'], capture_output=True, text=True, timeout=120)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('space', failed.stderr.lower())
            self.assertEqual(command('status', '--profile', profile)['state'], 'running',
                             'insufficient space must be detected before stopping the workstation')
            retained = json.loads(docker('exec', helper, '/tmp/workstation', 'backup', '--profile', '/tmp/profile',
                                        '--backup-directory', '/limited', '--list'))
            if len(retained['backups']) != 2:
                layout = docker('exec', helper, 'python3', '-c',
                    'from pathlib import Path; import json; rows=[]; '
                    '\nfor p in Path("/limited").iterdir():\n'
                    ' m=p/"manifest.json"; a=p/"home.tar"; d=json.loads(m.read_text()) if m.is_file() else {}; '
                    ' rows.append({"name":p.name,"directory":p.is_dir(),"symlink":p.is_symlink(),'
                    '"id":d.get("id"),"schema":d.get("schema"),"image":d.get("imageId"),'
                    '"expectedBytes":d.get("bytes"),"actualBytes":a.stat().st_size if a.is_file() else None,'
                    '"installation":d.get("profile",{}).get("installationId")})\nprint(json.dumps(rows))')
                (profile / 'limited-layout.json').write_text(json.dumps({'listed': retained,
                    'layout': json.loads(layout)}, indent=2), encoding='utf-8')
            self.assertEqual([entry['id'] for entry in retained['backups']], [copy['id'] for copy in reversed(copies)], retained)
            # An interrupted archive is rejected before touching the live installation.
            broken_root = profile / 'broken'
            broken = broken_root / copies[0]['id']
            broken.mkdir(parents=True)
            (broken / 'home.tar').write_bytes(b'incomplete')
            incomplete = invoke(CLI, 'restore', '--profile', profile, '--backup', broken)
            self.assertNotEqual(incomplete.returncode, 0)
            self.assertIn('incomplete', incomplete.stderr.lower())
            self.assertEqual(command('status', '--profile', profile)['state'], 'running')
            # A structurally invalid tar with valid length/hash exercises extraction failure.
            invalid_tar = b'not a tar archive\n' * 1024
            manifest = json.loads((Path(copies[0]['directory']) / 'manifest.json').read_text())
            manifest.update(bytes=len(invalid_tar), sha256=hashlib.sha256(invalid_tar).hexdigest())
            (broken / 'home.tar').write_bytes(invalid_tar)
            write_manifest(broken, manifest)
            original_profile = (profile / 'profile.json').read_bytes()
            rejected = invoke(CLI, 'restore', '--profile', profile, '--backup', broken)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('restore failed', rejected.stderr.lower())
            self.assertEqual((profile / 'profile.json').read_bytes(), original_profile)
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/important.txt'), 'keep current data')
            self.assertEqual([entry['id'] for entry in command('backup', '--profile', profile, '--list')['backups']],
                             [copy['id'] for copy in reversed(copies)])
            (profile / 'failure-result.json').write_text(json.dumps({'result': 'passed',
                'diskFull': 'rejected before interruption', 'incomplete': 'rejected',
                'invalidTar': 'original volume and profile preserved', 'validCopies': 2}, indent=2), encoding='utf-8')
        finally:
            for container in [helper, name]:
                subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', container], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            discard_backup_archives(profile / 'broken')

    def test_retention_is_per_installation_and_ignores_incomplete_attempts(self):
        suffix = uuid.uuid4().hex[:10]
        names = ['ew-backup-own-' + suffix, 'ew-backup-other-' + suffix]
        profiles = [ROOT / '.local' / name for name in names]
        storage = ROOT / '.local' / ('backups shared ' + suffix)
        try:
            for name, profile in zip(names, profiles):
                command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                        '--port', '13432', '--memory', '2560', '--cpus', '2', '--no-shortcut')
                command('start', '--profile', profile)
                command('backup', '--profile', profile, '--backup-directory', storage)
            original_other = command('backup', '--profile', profiles[1], '--backup-directory', storage, '--list')
            self.assertEqual(len(original_other['backups']), 1, 'each installation lists its own completed backups')
            incomplete = storage / '.incomplete-disposable-test'
            incomplete.mkdir()
            (incomplete / 'home.tar').write_bytes(b'interrupted archive')
            newest = []
            for marker in ['second', 'third']:
                command('start', '--profile', profiles[0])
                docker('exec', '--user', 'abc', names[0], 'python3', '-c',
                       'from pathlib import Path; import sys; Path("/config/projects/retained.txt").write_text(sys.argv[1])', marker)
                newest.append(command('backup', '--profile', profiles[0], '--backup-directory', storage))
            own = command('backup', '--profile', profiles[0], '--backup-directory', storage, '--list')
            self.assertEqual([entry['id'] for entry in own['backups']], [entry['id'] for entry in reversed(newest)])
            self.assertIn(incomplete.name, own['incomplete'])
            other = command('backup', '--profile', profiles[1], '--backup-directory', storage, '--list')
            self.assertEqual(other['backups'], original_other['backups'])
            self.assertEqual(len([p for p in storage.iterdir() if (p / 'manifest.json').is_file()]), 3)
            command('restore', '--profile', profiles[0], '--backup', newest[0]['directory'])
            command('start', '--profile', profiles[0])
            self.assertEqual(docker('exec', '--user', 'abc', names[0], 'cat', '/config/projects/retained.txt'), 'second')
            (profiles[0] / 'retention-result.json').write_text(json.dumps({'result': 'passed', 'ownBackups': own,
                'otherInstallationPreserved': True, 'olderRetainedCopyRestored': True}, indent=2), encoding='utf-8')
        finally:
            for name in names:
                subprocess.run(['docker', 'container', 'rm', '--force', name], capture_output=True)
                for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                    subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(storage)

    def test_restore_after_personal_volume_loss(self):
        name = 'ew-backup-loss-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        lost_tag = 'electivus/workstation-loss-test:' + uuid.uuid4().hex[:10]
        try:
            docker('image', 'tag', IMAGE, lost_tag)
            command('install', '--profile', profile, '--name', name, '--image', lost_tag,
                    '--port', '13431', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/recovered.txt").write_text("recover after volume loss")')
            saved = command('backup', '--profile', profile)
            docker('container', 'rm', name)
            docker('volume', 'rm', name + '-home')
            docker('image', 'rm', lost_tag)
            docker('image', 'inspect', saved['imageId'])
            recovered = command('restore', '--profile', profile, '--backup', saved['directory'])
            self.assertEqual(recovered['state'], 'restored')
            command('start', '--profile', profile)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/recovered.txt'),
                             'recover after volume loss')
            (profile / 'volume-loss-result.json').write_text(json.dumps({'result': 'passed', 'restore': recovered,
                'containerAndVolumeLost': True, 'oldTagRemoved': True, 'recordedImageAvailable': True}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            subprocess.run(['docker', 'image', 'rm', lost_tag], capture_output=True)

    def test_base_files_preferences_and_applications_restore(self):
        name = 'ew-backup-base-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / (name + ' with spaces')
        try:
            command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                    '--port', '13430', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            command('start', '--profile', profile)
            command('prepare', '--profile', profile)
            chrome_version = docker('exec', '--user', 'abc', name, 'google-chrome', '--version')
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; import os; p=Path("/config/projects/backup-project"); p.mkdir(); '
                   '(p/"run.sh").write_text("#!/bin/sh\\nprintf restored\\n"); (p/"run.sh").chmod(0o751); '
                   'os.utime(p/"run.sh", (1700000000, 1700000000)); (p/"RUN.sh").write_text("case-sensitive"); '
                   '(p/"link").symlink_to("run.sh"); os.link(p/"run.sh", p/"hardlink"); '
                   'os.setxattr(p/"run.sh", "user.workstation-test", b"preserved")')
            docker('exec', '--user', 'abc', name, 'plasma-apply-colorscheme', 'BreezeDark')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'kreadconfig6', '--file', 'kdeglobals',
                             '--group', 'General', '--key', 'ColorScheme'), 'BreezeDark')
            saved = command('backup', '--profile', profile)
            self.assertEqual(saved['state'], 'completed')
            self.assertEqual(command('status', '--profile', profile)['state'], 'stopped')
            listed = command('backup', '--profile', profile, '--list')
            self.assertEqual([entry['id'] for entry in listed['backups']], [saved['id']])
            self.assertTrue(Path(saved['directory']).is_dir())
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; p=Path("/config/projects/backup-project"); '
                   '(p/"run.sh").write_text("changed"); (p/"link").unlink(); (p/"RUN.sh").unlink()')
            docker('exec', '--user', 'abc', name, 'plasma-apply-colorscheme', 'BreezeLight')
            restored = command('restore', '--profile', profile, '--backup', saved['directory'])
            self.assertEqual(restored['state'], 'restored')
            command('start', '--profile', profile)
            files = json.loads(docker('exec', '--user', 'abc', name, 'python3', '-c',
                'from pathlib import Path; import json,os; p=Path("/config/projects/backup-project"); s=(p/"run.sh").stat(); '
                'print(json.dumps({"content":(p/"run.sh").read_text(), "case":(p/"RUN.sh").read_text(), '
                '"mode":oct(s.st_mode & 0o777), "uid":s.st_uid,"gid":s.st_gid,"mtime":int(s.st_mtime),'
                '"symlink":os.readlink(p/"link"),"hardlink":s.st_ino==(p/"hardlink").stat().st_ino,'
                '"xattr":os.getxattr(p/"run.sh", "user.workstation-test").decode()}))'))
            self.assertEqual(files, {'content': '#!/bin/sh\nprintf restored\n', 'case': 'case-sensitive',
                'mode': '0o751', 'uid': 1000, 'gid': 1000, 'mtime': 1700000000, 'symlink': 'run.sh', 'hardlink': True,
                'xattr': 'preserved'})
            self.assertEqual(docker('exec', '--user', 'abc', name, 'kreadconfig6', '--file', 'kdeglobals',
                             '--group', 'General', '--key', 'ColorScheme'), 'BreezeDark')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'google-chrome', '--version'), chrome_version)
            (profile / 'backup-result.json').write_text(json.dumps({'result': 'passed', 'files': files,
                'chrome': chrome_version, 'backup': saved, 'restore': restored}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', name], capture_output=True)
            volumes = docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines()
            for volume in volumes:
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')

    def test_new_installation_has_no_backups(self):
        name = 'ew-backup-list-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / (name + ' with spaces')
        command('install', '--profile', profile, '--name', name, '--image', IMAGE,
                '--memory', '2560', '--cpus', '2', '--no-shortcut')
        result = command('backup', '--profile', profile, '--list')
        self.assertEqual(result['backups'], [])
        self.assertEqual(command('status', '--profile', profile)['state'], 'installed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
