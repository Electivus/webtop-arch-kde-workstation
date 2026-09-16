"""Selected image identity and explicit maintenance through delivered commands."""
import json
import os
import subprocess
import time
import unittest
import uuid

import test_updates
from test_commands import ROOT, CLI, command, docker, invoke
from test_backups import discard_backup_archives
from test_packages import configure_test_network, install_local_fixture, write_build_source
from test_updates import chrome_page

BASE = os.environ.get('WORKSTATION_TEST_IMAGE', 'electivus/webtop-arch-kde-base:t09-t10')
REGISTRY = 'registry@sha256:1be55279f18a2fe1a74edf2664cac61c1bea305b7b4642dab412e7affdcb3e33'


class ImageUpdateAcceptance(unittest.TestCase):
    def build_image(self, profile, tag, version, broken_git=False):
        profile.mkdir(parents=True, exist_ok=True)
        built = subprocess.run(['docker', 'build', '--build-arg', 'BASE_IMAGE=' + BASE,
            '--build-arg', 'WORKSTATION_VERSION=' + version,
            '--build-arg', 'BROKEN_GIT=' + ('1' if broken_git else '0'), '--tag', tag,
            str(ROOT / 'tests/fixtures/image-updates')],
            capture_output=True, text=True, encoding='utf-8', timeout=180)
        (profile / (version + '-build.log')).write_text(built.stdout + built.stderr, encoding='utf-8')
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
        return json.loads(docker('image', 'inspect', tag))[0]['Id']

    def test_an_older_profile_adopts_the_running_image_before_recreation(self):
        name = 'ew-image-legacy-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate, stable = [name + ':' + tag for tag in ['7.0.0', '7.1.0', 'stable']]
        try:
            original_id = self.build_image(profile, original, '7.0.0-t09')
            self.build_image(profile, candidate, '7.1.0-t09')
            docker('image', 'tag', original, stable)
            command('install', '--profile', profile, '--name', name, '--image', stable,
                    '--port', '13464', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/legacy.txt").write_text("older personal profile")')
            current = json.loads((profile / 'profile.json').read_text(encoding='utf-8'))
            # This is the schema-1 profile shape emitted before T09. It has a
            # chosen reference and no persisted image identifier.
            legacy = {key: current[key] for key in ['schema', 'installationId', 'name', 'image', 'port',
                'memoryMiB', 'cpus', 'homeVolume', 'dockerContext', 'exchange'] if key in current}
            (profile / 'profile.json').write_text(json.dumps(legacy, indent=2), encoding='utf-8')
            docker('image', 'tag', candidate, stable)
            adopted = command('start', '--profile', profile)
            self.assertEqual(adopted['containerId'], before['containerId'])
            self.assertEqual(adopted['imageId'], original_id)
            docker('container', 'rm', '--force', name)
            recreated = command('start', '--profile', profile)
            self.assertEqual(recreated['imageId'], original_id)
            self.assertEqual(recreated['version'], '7.0.0-t09')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/legacy.txt'), 'older personal profile')
            (profile / 'legacy-selection-result.json').write_text(json.dumps({'result': 'passed',
                'legacyProfile': legacy, 'adopted': adopted, 'recreated': recreated}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            for tag in [stable, candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_lost_legacy_container_requires_recovery_before_using_its_existing_home(self):
        name = 'ew-image-legacy-lost-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate, stable = [name + ':' + tag for tag in ['8.0.0', '8.1.0', 'stable']]
        try:
            original_id = self.build_image(profile, original, '8.0.0-t09')
            self.build_image(profile, candidate, '8.1.0-t09')
            docker('image', 'tag', original, stable)
            command('install', '--profile', profile, '--name', name, '--image', stable,
                    '--port', '13465', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/legacy.txt").write_text("recover my original workstation")')
            legacy = json.loads((profile / 'profile.json').read_text(encoding='utf-8'))
            legacy.pop('imageId')
            (profile / 'profile.json').write_text(json.dumps(legacy, indent=2), encoding='utf-8')
            saved = command('backup', '--profile', profile)
            docker('image', 'tag', candidate, stable)
            docker('container', 'rm', '--force', name)
            rejected = {}
            for action in [('start',), ('backup',), ('update-image', '--image', candidate, '--pull=false')]:
                attempt = invoke(CLI, *action, '--profile', profile)
                self.assertNotEqual(attempt.returncode, 0, 'An unknown original image must not be silently replaced')
                self.assertIn('original image', attempt.stderr.lower())
                rejected[action[0]] = attempt.stderr.strip()
                self.assertEqual(docker('container', 'ls', '--all', '--quiet', '--filter', 'name=^/' + name + '$'), '')
                self.assertNotIn('imageId', json.loads((profile / 'profile.json').read_text(encoding='utf-8')))
            recovered = command('restore', '--profile', profile, '--backup', saved['directory'])
            restarted = command('start', '--profile', profile)
            self.assertEqual(restarted['imageId'], original_id)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/legacy.txt'),
                             'recover my original workstation')
            (profile / 'lost-legacy-result.json').write_text(json.dumps({'result': 'passed',
                'rejected': rejected, 'recovery': recovered, 'restarted': restarted}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [stable, candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_registry_tag_and_digest_are_resolved_only_by_explicit_updates(self):
        name = 'ew-image-registry-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate = name + ':6.0.0', name + ':6.1.0'
        registry = name + '-registry'
        port = str(15000 + int(uuid.uuid4().hex[:4], 16) % 10000)
        repository = '127.0.0.1:' + port + '/workstation'
        stable = repository + ':stable'
        remote_tags = [stable, repository + ':6.0.0', repository + ':6.1.0']
        probe_source = (ROOT / 'tests/registry_probe.py').read_text(encoding='utf-8')

        def get(resource):
            return json.loads(docker('run', '--rm', '--network', 'host', '--memory', '128m',
                '--read-only', '--entrypoint', 'python3', BASE, '-c', probe_source,
                'http://127.0.0.1:' + port + resource))

        def push(source, target, phase):
            docker('image', 'tag', source, target)
            result = subprocess.run(['docker', 'push', target], capture_output=True,
                                    text=True, encoding='utf-8', timeout=600)
            (profile / (phase + '-push.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        try:
            original_id = self.build_image(profile, original, '6.0.0-t09')
            candidate_id = self.build_image(profile, candidate, '6.1.0-t09')
            docker('run', '--detach', '--name', registry, '--network', 'host', '--memory', '1024m',
                   '--cpus', '1', '--env', 'GOMEMLIMIT=768MiB',
                   '--env', 'REGISTRY_HTTP_ADDR=127.0.0.1:' + port, REGISTRY)
            deadline = time.monotonic() + 20
            while True:
                try:
                    self.assertEqual(get('/v2/')['status'], 200)
                    break
                except AssertionError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.2)
            push(original, remote_tags[1], 'original-fixed')
            push(original, stable, 'original-stable')
            old_manifest = get('/v2/workstation/manifests/6.0.0')
            old_digest = old_manifest['headers']['docker-content-digest']
            self.assertEqual(old_digest, old_manifest['sha256'])
            command('install', '--profile', profile, '--name', name, '--image', stable,
                    '--port', '13463', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            self.assertEqual(before['imageId'], original_id)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Project survives registry selections</h1>")')
            push(candidate, remote_tags[2], 'candidate-fixed')
            push(candidate, stable, 'candidate-stable')
            new_manifest = get('/v2/workstation/manifests/stable')
            new_digest = new_manifest['headers']['docker-content-digest']
            self.assertEqual(new_digest, new_manifest['sha256'])
            self.assertNotEqual(new_digest, old_digest)
            # Leave the local tag stale while the registry advertises the new
            # version. The default update must really fetch its selection.
            docker('image', 'tag', original, stable)
            self.assertEqual(json.loads(docker('image', 'inspect', stable))[0]['Id'], original_id)
            command('stop', '--profile', profile)
            self.assertEqual(command('start', '--profile', profile)['imageId'], original_id)
            tag_attempt = invoke(CLI, 'update-image', '--profile', profile, '--image', stable, timeout=2100)
            (profile / 'tag-update.log').write_text(tag_attempt.stdout + tag_attempt.stderr, encoding='utf-8')
            self.assertEqual(tag_attempt.returncode, 0, tag_attempt.stdout + tag_attempt.stderr)
            tag_update = json.loads(tag_attempt.stdout)
            self.assertTrue(tag_update['usable'], tag_update)
            self.assertEqual(tag_update['selected']['imageId'], candidate_id)
            self.assertEqual(tag_update['selected']['version'], '6.1.0-t09')
            self.assertIn(repository + '@' + new_digest, tag_update['selected']['repositoryDigests'])
            self.assertEqual(command('status', '--profile', profile)['imageId'], candidate_id)
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Project survives registry selections', chrome_page(name))
            pinned_reference = repository + '@' + old_digest
            digest_attempt = invoke(CLI, 'update-image', '--profile', profile, '--image', pinned_reference, timeout=2100)
            (profile / 'digest-update.log').write_text(digest_attempt.stdout + digest_attempt.stderr, encoding='utf-8')
            self.assertEqual(digest_attempt.returncode, 0, digest_attempt.stdout + digest_attempt.stderr)
            digest_update = json.loads(digest_attempt.stdout)
            self.assertTrue(digest_update['usable'], digest_update)
            self.assertEqual(digest_update['selected']['image'], pinned_reference)
            self.assertEqual(digest_update['selected']['imageId'], original_id)
            self.assertEqual(digest_update['selected']['version'], '6.0.0-t09')
            self.assertIn(pinned_reference, digest_update['selected']['repositoryDigests'])
            self.assertEqual(command('status', '--profile', profile)['imageId'], original_id)
            self.assertIn('Project survives registry selections', chrome_page(name))
            (profile / 'registry-selection-result.json').write_text(json.dumps({'result': 'passed',
                'externalPublication': False, 'registryImage': REGISTRY,
                'oldManifest': old_manifest, 'newManifest': new_manifest,
                'tagUpdate': tag_update, 'digestUpdate': digest_update}, indent=2), encoding='utf-8')
        finally:
            for filename, arguments in [('registry-inspect.json', ['inspect']), ('registry.log', ['logs'])]:
                diagnostic = subprocess.run(['docker', *arguments, registry], capture_output=True,
                                            text=True, encoding='utf-8', errors='replace', timeout=30)
                if profile.is_dir():
                    (profile / filename).write_text(diagnostic.stdout + diagnostic.stderr, encoding='utf-8')
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [*remote_tags, candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', registry], capture_output=True)

    def test_an_extra_build_failure_keeps_the_updated_environment_usable_and_allows_retry(self):
        name = 'ew-image-extra-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate = name + ':5.0.0', name + ':5.1.0'
        source = '/config/projects/personal-tool'
        try:
            self.build_image(profile, original, '5.0.0-t09')
            candidate_id = self.build_image(profile, candidate, '5.1.0-t09')
            command('install', '--profile', profile, '--name', name, '--image', original,
                    '--port', '13462', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Project remains usable after an extra fails</h1>")')
            docker('exec', name, 'workstation-network', 'exec', '--', 'pacman', '-Syu', '--needed',
                   '--disable-download-timeout', '--noprogressbar', '--noconfirm', 'figlet')
            install_local_fixture(name, source)
            command('packages', '--profile', profile, '--register', 'workstation-local-example', '--source', source)
            write_build_source(name, source, '#error personal tool needs correction before rebuilding\n')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'workstation-local-example'), 'workstation local example')
            attempted = invoke(CLI, 'update-image', '--profile', profile, '--image', candidate, '--pull=false', timeout=2100)
            (profile / 'extra-failure-attempt.log').write_text(attempted.stdout + attempted.stderr, encoding='utf-8')
            self.assertEqual(attempted.returncode, 0, attempted.stdout + attempted.stderr)
            updated = json.loads(attempted.stdout)
            self.assertEqual(updated['state'], 'partial', updated)
            self.assertTrue(updated['usable'], updated)
            self.assertEqual(updated['selected']['imageId'], candidate_id)
            self.assertEqual(updated['backup']['state'], 'completed')
            self.assertEqual(set(updated['checks']), {'desktop', 'git', 'shell', 'terminal', 'docker', 'browser'})
            self.assertTrue(all(check['state'] == 'passed' for check in updated['checks'].values()))
            extras = {entry['name']: entry for entry in updated['packages']['packages']}
            self.assertEqual(extras['figlet']['state'], 'restored')
            for package in ['workstation-local-example', 'workstation-local-example-debug']:
                self.assertEqual(extras[package]['state'], 'build-failed')
                self.assertIn('personal tool needs correction', extras[package]['diagnostic'])
            self.assertEqual(command('packages', '--profile', profile)['lastRestore'], updated['packages'])
            self.assertTrue(command('status', '--profile', profile)['healthy'])
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Project remains usable after an extra fails', chrome_page(name))
            docker('exec', '--user', 'abc', name, 'figlet', 'still working')
            self.assertIn(updated['backup']['id'], [item['id'] for item in command('backup', '--profile', profile, '--list')['backups']])
            write_build_source(name, source, (ROOT / 'tests/fixtures/extra-package/example.c').read_text())
            retried = command('packages', '--profile', profile, '--restore')
            self.assertEqual(retried['state'], 'completed', retried)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'workstation-local-example'), 'workstation local example')
            self.assertEqual(command('status', '--profile', profile)['imageId'], candidate_id)
            self.assertEqual(command('update-image', '--profile', profile, '--status'), updated)
            (profile / 'extra-failure-result.json').write_text(json.dumps({'result': 'passed',
                'update': updated, 'retry': retried}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_a_broken_provided_component_cannot_be_declared_usable_and_can_be_recovered(self):
        name = 'ew-image-core-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate = name + ':4.0.0', name + ':4.1.0'
        try:
            original_id = self.build_image(profile, original, '4.0.0-t09')
            candidate_id = self.build_image(profile, candidate, '4.1.0-t09', broken_git=True)
            command('install', '--profile', profile, '--name', name, '--image', original,
                    '--port', '13461', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Project before a broken image</h1>")')
            attempted = invoke(CLI, 'update-image', '--profile', profile, '--image', candidate, '--pull=false', timeout=2100)
            (profile / 'provided-failure-attempt.log').write_text(attempted.stdout + attempted.stderr, encoding='utf-8')
            self.assertNotEqual(attempted.returncode, 0)
            failed = command('update-image', '--profile', profile, '--status')
            self.assertEqual(failed['state'], 'failed', failed)
            self.assertFalse(failed['usable'], failed)
            self.assertEqual(failed['step'], 'checks')
            self.assertEqual(failed['checks']['git']['state'], 'failed')
            self.assertIn('git failed verification', failed['error'])
            self.assertEqual(failed['selected']['imageId'], candidate_id)
            self.assertEqual(failed['previous']['imageId'], original_id)
            self.assertEqual(failed['backup']['state'], 'completed')
            self.assertEqual(command('status', '--profile', profile)['imageId'], candidate_id)
            self.assertTrue(docker('exec', name, 'pacman', '-Q', 'git').startswith('git '))
            # The package record remains installed, but its public executable
            # really fails. A package inventory alone cannot approve this image.
            probe = subprocess.run(['docker', 'exec', '--user', 'abc', name, 'git', '--version'], capture_output=True)
            self.assertEqual(probe.returncode, 73)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text("changed while inspecting failure")')
            recovered = command('restore', '--profile', profile, '--backup', failed['backup']['directory'])
            restored = command('start', '--profile', profile)
            self.assertEqual(restored['imageId'], original_id)
            self.assertEqual(restored['version'], '4.0.0-t09')
            self.assertTrue(docker('exec', '--user', 'abc', name, 'git', '--version').startswith('git version '))
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertIn('Project before a broken image', chrome_page(name))
            self.assertEqual(command('update-image', '--profile', profile, '--status'), failed)
            (profile / 'provided-failure-result.json').write_text(json.dumps({'result': 'passed',
                'update': failed, 'recovery': recovered, 'restored': restored}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_image_backup_failures_preserve_the_original_running_environment(self):
        name = 'ew-image-backup-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate = name + ':3.0.0', name + ':3.1.0'
        try:
            original_id = self.build_image(profile, original, '3.0.0-t09')
            self.build_image(profile, candidate, '3.1.0-t09')
            command('install', '--profile', profile, '--name', name, '--image', original,
                    '--port', '13460', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            original_profile = (profile / 'profile.json').read_bytes()
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text('
                   '"<h1>Original image project</h1>")')
            blocked = profile / 'not-a-backup-directory'
            blocked.write_text('preserve the existing file', encoding='utf-8')
            results = []
            for phase in ['before-stop', 'after-stop']:
                started_at = json.loads(docker('inspect', name))[0]['State']['StartedAt']
                arguments = ['--backup-directory', blocked] if phase == 'before-stop' else []
                if phase == 'after-stop':
                    (profile / 'certificates' / 'broken.crt').write_text('damaged archived certificate', encoding='utf-8')
                    settings = {'proxy': 'http://127.0.0.1:9'}
                    if os.environ.get('WORKSTATION_TEST_CA_FILE'):
                        settings['caFiles'] = [os.environ['WORKSTATION_TEST_CA_FILE']]
                    pending = profile / 'pending-network.json'
                    pending.write_text(json.dumps(settings), encoding='utf-8')
                    command('network', '--profile', profile, '--network-config', pending)
                attempted = invoke(CLI, 'update-image', '--profile', profile, '--image', candidate,
                                   '--pull=false', *arguments, timeout=2100)
                self.assertNotEqual(attempted.returncode, 0)
                failed = command('update-image', '--profile', profile, '--status')
                self.assertEqual(failed['state'], 'failed')
                self.assertEqual(failed['step'], 'backup')
                self.assertNotIn('packages', failed)
                self.assertNotIn('checks', failed)
                self.assertEqual(failed['previous']['imageId'], original_id)
                deadline = time.monotonic() + 90
                after = command('status', '--profile', profile)
                while not after['healthy'] and time.monotonic() < deadline:
                    time.sleep(1)
                    after = command('status', '--profile', profile)
                self.assertTrue(after['healthy'], after)
                self.assertEqual(after['containerId'], before['containerId'])
                self.assertEqual(after['imageId'], original_id)
                self.assertEqual((profile / 'profile.json').read_bytes(), original_profile)
                self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
                self.assertIn('Original image project', chrome_page(name))
                current_started = json.loads(docker('inspect', name))[0]['State']['StartedAt']
                if phase == 'before-stop':
                    self.assertEqual(current_started, started_at)
                else:
                    self.assertNotEqual(current_started, started_at)
                    self.assertIn('invalid local certificate archive', failed['error'])
                    docker('exec', '--user', 'abc', name, 'workstation-network', 'exec', '--', 'curl',
                           '--fail', '--silent', '--head', '--max-time', '30',
                           'https://dl.google.com/linux/chrome/deb/dists/stable/Release')
                results.append({'phase': phase, 'report': failed})
            self.assertEqual(blocked.read_text(), 'preserve the existing file')
            self.assertEqual(command('backup', '--profile', profile, '--list')['backups'], [])
            (profile / 'image-backup-failures-result.json').write_text(json.dumps({'result': 'passed',
                'attempts': results}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_explicit_image_update_restores_extras_and_recovers_the_previous_project(self):
        name = 'ew-image-update-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate, stable = [name + ':' + tag for tag in ['2.0.0', '2.1.0', 'stable']]
        source = '/config/projects/personal-tool'
        try:
            salesforce_variant = json.loads(docker('image', 'inspect', BASE))[0]['Config']['Labels'][
                'io.electivus.workstation.variant'] == 'salesforce'
            memory = '6144' if salesforce_variant else '2560'
            cpus = str(min(4, int(docker('info', '--format', '{{.NCPU}}')))) if salesforce_variant else '2'
            project_title = 'Salesforce maintenance project' if salesforce_variant else 'Personal project before image update'
            original_id = self.build_image(profile, original, '2.0.0-t09')
            candidate_id = self.build_image(profile, candidate, '2.1.0-t09')
            docker('image', 'tag', original, stable)
            command('install', '--profile', profile, '--name', name, '--image', stable,
                    '--port', '13459', '--memory', memory, '--cpus', cpus, '--no-shortcut')
            configure_test_network(profile)
            before = command('start', '--profile', profile)
            prepared = command('prepare', '--profile', profile)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; import sys; Path("/config/projects/maintenance.html").write_text(sys.argv[1])',
                   '<h1>' + project_title + '</h1>')
            if salesforce_variant:
                generated = json.loads(docker('exec', '--user', 'abc', name, 'sf', 'project', 'generate',
                    '--name', 'maintenance-sf', '--output-dir', '/config/projects', '--json'))
                self.assertEqual(generated['status'], 0, generated)
                project_config = docker('exec', '--user', 'abc', name, 'cat', '/config/projects/maintenance-sf/sfdx-project.json')
            docker('exec', name, 'workstation-network', 'exec', '--', 'pacman', '-Syu', '--needed',
                   '--disable-download-timeout', '--noprogressbar', '--noconfirm', 'figlet')
            install_local_fixture(name, source)
            command('packages', '--profile', profile, '--register', 'workstation-local-example', '--source', source)
            docker('image', 'tag', candidate, stable)
            expected_digests = json.loads(docker('image', 'inspect', stable))[0].get('RepoDigests') or []
            attempted = invoke(CLI, 'update-image', '--profile', profile, '--image', stable, '--pull=false', timeout=2100)
            (profile / 'image-update-attempt.log').write_text(attempted.stdout + attempted.stderr, encoding='utf-8')
            self.assertEqual(attempted.returncode, 0, attempted.stdout + attempted.stderr)
            updated = json.loads(attempted.stdout)
            (profile / 'image-update-attempt.json').write_text(json.dumps(updated, indent=2), encoding='utf-8')
            self.assertEqual(updated['state'], 'completed', updated)
            self.assertTrue(updated['usable'], updated)
            self.assertEqual(updated['previous']['imageId'], original_id)
            self.assertEqual(updated['previous']['version'], '2.0.0-t09')
            self.assertEqual(updated['selected']['imageId'], candidate_id)
            self.assertEqual(updated['selected']['version'], '2.1.0-t09')
            self.assertEqual(updated['selected']['repositoryDigests'], expected_digests)
            self.assertEqual(updated['backup']['state'], 'completed')
            self.assertEqual(updated['backup']['imageId'], original_id)
            self.assertEqual(updated['checks']['git']['state'], 'passed')
            self.assertEqual(updated['checks']['git']['output'], docker('exec', '--user', 'abc', name, 'git', '--version'))
            self.assertEqual(updated['packages']['state'], 'completed')
            extras = {entry['name']: entry for entry in updated['packages']['packages']}
            self.assertEqual(extras['figlet']['state'], 'restored')
            self.assertEqual(extras['workstation-local-example']['method'], 'rebuilt')
            docker('exec', '--user', 'abc', name, 'figlet', 'updated')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'workstation-local-example'), 'workstation local example')
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            after = command('status', '--profile', profile)
            self.assertTrue(after['healthy'])
            self.assertEqual(after['imageId'], candidate_id)
            self.assertNotEqual(after['containerId'], before['containerId'])
            for setting in ['limits', 'url', 'homeVolume', 'storage']:
                self.assertEqual(after[setting], before[setting])
            self.assertIn(project_title, chrome_page(name))
            if salesforce_variant:
                self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/maintenance-sf/sfdx-project.json'), project_config)
                test_updates.UpdateAcceptance.exercise_salesforce_project(self, name, profile, 'image-updated')
            self.assertEqual(command('update-image', '--profile', profile, '--status'), updated)
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/maintenance.html").write_text("changed after image update")')
            recovered = command('restore', '--profile', profile, '--backup', updated['backup']['directory'])
            restored = command('start', '--profile', profile)
            self.assertEqual(restored['imageId'], original_id)
            self.assertEqual(restored['version'], '2.0.0-t09')
            self.assertEqual(command('prepare', '--profile', profile)['apps'], prepared['apps'])
            self.assertEqual(command('packages', '--profile', profile, '--restore')['state'], 'completed')
            self.assertEqual(docker('exec', '--user', 'abc', name, 'workstation-local-example'), 'workstation local example')
            docker('exec', '--user', 'abc', name, 'figlet', 'recovered')
            self.assertIn(project_title, chrome_page(name))
            if salesforce_variant:
                self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/maintenance-sf/sfdx-project.json'), project_config)
                test_updates.UpdateAcceptance.exercise_salesforce_project(self, name, profile, 'image-restored')
            self.assertEqual(command('update-image', '--profile', profile, '--status'), updated)
            (profile / 'image-update-result.json').write_text(json.dumps({'result': 'passed',
                'update': updated, 'recovery': recovered, 'restored': restored}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            for volume in docker('volume', 'ls', '--filter', 'name=' + name + '-home', '--format', '{{.Name}}').splitlines():
                subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            discard_backup_archives(profile / 'backups')
            for tag in [stable, candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)

    def test_moving_stable_preserves_selection_after_container_loss(self):
        name = 'ew-image-pin-' + uuid.uuid4().hex[:10]
        profile = ROOT / '.local' / name
        original, candidate, stable = [name + ':' + tag for tag in ['1.0.0', '1.1.0', 'stable']]
        try:
            original_id = self.build_image(profile, original, '1.0.0-t09')
            candidate_id = self.build_image(profile, candidate, '1.1.0-t09')
            self.assertNotEqual(candidate_id, original_id)
            docker('image', 'tag', original, stable)
            command('install', '--profile', profile, '--name', name, '--image', stable,
                    '--port', '13458', '--memory', '2560', '--cpus', '2', '--no-shortcut')
            configure_test_network(profile)
            selected = command('start', '--profile', profile)
            self.assertEqual(selected['imageId'], original_id)
            self.assertEqual(selected['version'], '1.0.0-t09')
            docker('exec', '--user', 'abc', name, 'python3', '-c',
                   'from pathlib import Path; Path("/config/projects/selection.txt").write_text("keep my selected image")')
            docker('image', 'tag', candidate, stable)
            command('stop', '--profile', profile)
            self.assertEqual(command('start', '--profile', profile)['imageId'], original_id)
            docker('container', 'rm', '--force', name)
            recreated = command('start', '--profile', profile)
            (profile / 'selection-attempt.json').write_text(json.dumps(recreated, indent=2), encoding='utf-8')
            self.assertEqual(recreated['imageId'], original_id,
                             'Moving stable must not select a new image when the container is recreated')
            self.assertEqual(recreated['image'], stable)
            self.assertEqual(docker('exec', '--user', 'abc', name, 'cat', '/config/projects/selection.txt'),
                             'keep my selected image')
            # An unavailable selected image must fail instead of falling forward
            # to the now-different alias. The personal volume remains available.
            docker('container', 'rm', '--force', name)
            docker('image', 'rm', original)
            unavailable = invoke(CLI, 'start', '--profile', profile)
            self.assertNotEqual(unavailable.returncode, 0)
            self.assertIn(original_id, unavailable.stderr)
            self.assertEqual(command('status', '--profile', profile)['state'], 'installed')
            self.assertEqual(json.loads(docker('volume', 'inspect', name + '-home'))[0]['Name'], name + '-home')
            (profile / 'selection-result.json').write_text(json.dumps({'result': 'passed',
                'selected': selected, 'recreated': recreated, 'unavailable': unavailable.stderr}, indent=2), encoding='utf-8')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--force', '--volumes', name], capture_output=True)
            subprocess.run(['docker', 'volume', 'rm', name + '-home'], capture_output=True)
            for tag in [stable, candidate, original]:
                subprocess.run(['docker', 'image', 'rm', tag], capture_output=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
