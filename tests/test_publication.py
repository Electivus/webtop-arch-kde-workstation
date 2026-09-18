"""Publication decisions through the CLI and the registry protocol boundary."""
import hashlib
import json
import os
import contextlib
import socket
import shutil
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_IMAGE = 'registry@sha256:1be55279f18a2fe1a74edf2664cac61c1bea305b7b4642dab412e7affdcb3e33'


def run(*arguments, env=None):
    result = subprocess.run(list(map(str, arguments)), cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


class PublicationAcceptance(unittest.TestCase):
    @contextlib.contextmanager
    def registry_pair(self):
        with tempfile.TemporaryDirectory(prefix='publication-pair-') as temporary:
            directory = Path(temporary)
            candidate, validation, checks = self.approved_metadata(directory)
            version = 'publication-' + uuid.uuid4().hex[:12]
            tags = ['electivus/webtop-arch-kde-' + variant + ':' + version for variant in ('base', 'salesforce')]
            name = 'ew-' + version
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
            registry = '127.0.0.1:' + str(port)
            config = directory / 'docker-config'
            config.mkdir()
            environment = dict(os.environ, DOCKER_CONFIG=str(config))
            try:
                (directory / 'marker').write_text(version)
                (directory / 'base.Dockerfile').write_text('''FROM scratch
ARG VERSION
ARG REVISION
LABEL org.opencontainers.image.version="${VERSION}" org.opencontainers.image.revision="${REVISION}" io.electivus.workstation.variant="base"
COPY marker /marker
''')
                (directory / 'salesforce.Dockerfile').write_text('''ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG BASE_DIGEST
LABEL io.electivus.workstation.variant="salesforce" org.opencontainers.image.base.name="${BASE_IMAGE}" org.opencontainers.image.base.digest="${BASE_DIGEST}"
COPY marker /salesforce-marker
''')
                base_digest = None
                for index, variant in enumerate(('base', 'salesforce')):
                    archive = directory / ('webtop-arch-kde-' + variant + '.oci.tar')
                    arguments = ['docker', 'buildx', 'build', '--platform', 'linux/amd64', '--provenance=mode=min',
                                 '--file', directory / (variant + '.Dockerfile'), '--tag', tags[index],
                                 '--output', 'type=oci,dest=' + str(archive), '--build-arg', 'VERSION=' + version,
                                 '--build-arg', 'REVISION=' + candidate['revision']]
                    if index:
                        arguments += ['--build-arg', 'BASE_IMAGE=' + tags[0], '--build-arg', 'BASE_DIGEST=' + base_digest]
                    run(*arguments, directory, env=environment)
                    run('docker', 'load', '--input', archive, env=environment)
                    if not index:
                        base_digest = run('docker', 'image', 'inspect', tags[0], '--format', '{{.Id}}', env=environment).strip()
                commands = directory / 'commands'
                (commands / 'licenses').mkdir(parents=True)
                for filename in ('setup.cmd', 'workstation.cmd', 'workstation.exe', 'workstation',
                                 'licenses/ELECTIVUS-LICENSE', 'licenses/THIRD-PARTY.md',
                                 'licenses/GO-LICENSE', 'licenses/MOBY-LICENSE'):
                    (commands / filename).write_text('Candidate transport fixture: ' + filename)
                with tarfile.open(directory / 'commands.tar', 'w') as archive:
                    archive.add(commands, arcname='commands')
                (directory / 'candidate.json').unlink()
                candidate = json.loads(run(sys.executable, 'scripts/candidate.py', 'record', '--directory', directory,
                                           '--version', version, '--revision', candidate['revision'], env=environment))
                validation.update(version=version, digests=[image['digest'] for image in candidate['images']])
                (directory / 'validation/validation.json').write_text(json.dumps(validation))
                run('docker', 'run', '--detach', '--name', name, '--network', 'host', '--memory', '256m',
                    '--env', 'REGISTRY_HTTP_ADDR=127.0.0.1:' + str(port), REGISTRY_IMAGE, env=environment)
                deadline = time.monotonic() + 30
                while True:
                    try:
                        with urllib.request.urlopen('http://' + registry + '/v2/', timeout=2):
                            break
                    except (OSError, urllib.error.URLError):
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.2)
                yield directory, candidate, registry, environment
            finally:
                subprocess.run(['docker', 'rm', '--force', '--volumes', name], capture_output=True)
                for tag in tags:
                    repository = tag.split(':')[0]
                    for reference in (tag, registry + '/' + tag, registry + '/' + repository + ':stable'):
                        subprocess.run(['docker', 'image', 'rm', reference], capture_output=True)

    def approved_metadata(self, directory):
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        contract = subprocess.check_output(['git', 'show', revision + ':tests/acceptance.json'], cwd=ROOT)
        (directory / 'validation/checks').mkdir(parents=True)
        candidate = {'schemaVersion': 1, 'state': 'built', 'architecture': 'linux/amd64',
                     'version': 'publication-proof', 'revision': revision,
                     'images': [{'variant': variant, 'digest': 'sha256:' + str(index) * 64,
                                 'reference': 'electivus/webtop-arch-kde-' + variant + ':publication-proof'}
                                for index, variant in enumerate(('base', 'salesforce'), 1)]}
        validation = {'state': 'passed', 'approved': True, 'failureProof': False,
                      'version': candidate['version'], 'revision': revision, 'validatorRevision': revision,
                      'digests': [image['digest'] for image in candidate['images']],
                      'contractSha256': hashlib.sha256(contract).hexdigest()}
        checks = {'state': 'passed', 'contractSha256': validation['contractSha256'],
                  'checks': [{'id': check['id'], 'state': 'passed', 'exitCode': 0}
                             for check in json.loads(contract)['checks']]}
        for name, data in [('candidate.json', candidate), ('validation/validation.json', validation),
                           ('validation/checks/acceptance.json', checks)]:
            (directory / name).write_text(json.dumps(data))
        return candidate, validation, checks

    def test_failed_acceptance_cannot_publish_or_promote_stable(self):
        with tempfile.TemporaryDirectory(prefix='publication-rejected-') as temporary:
            directory = Path(temporary)
            (directory / 'validation').mkdir()
            (directory / 'candidate.json').write_text(json.dumps({
                'schemaVersion': 1, 'version': '1.0.0', 'revision': '1' * 40,
                'images': [{'variant': variant, 'digest': 'sha256:' + str(index) * 64}
                           for index, variant in enumerate(('base', 'salesforce'), 1)]}))
            (directory / 'validation/validation.json').write_text(json.dumps({
                'state': 'failed', 'approved': False, 'failureProof': True}))
            report = directory / 'publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', report],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(report.exists(), result.stderr)
            receipt = json.loads(report.read_text())
            self.assertEqual(receipt['state'], 'rejected')
            self.assertFalse(receipt['complete'])
            self.assertEqual(receipt['operations'], [])
            self.assertIn('acceptance', receipt['error'].lower())

    def test_approval_flag_cannot_hide_an_incomplete_acceptance_contract(self):
        with tempfile.TemporaryDirectory(prefix='publication-incomplete-') as temporary:
            directory = Path(temporary)
            _, _, checks = self.approved_metadata(directory)
            checks['checks'][-1]['state'] = 'failed'
            checks['checks'][-1]['exitCode'] = 1
            (directory / 'validation/checks/acceptance.json').write_text(json.dumps(checks))
            report = directory / 'publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', report],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            receipt = json.loads(report.read_text())
            self.assertEqual(receipt['state'], 'rejected')
            self.assertFalse(receipt['complete'])
            self.assertEqual(receipt['operations'], [])
            self.assertIn('complete acceptance contract', receipt['error'].lower())

    def test_docker_hub_versions_must_match_the_protected_numeric_tag_policy(self):
        with tempfile.TemporaryDirectory(prefix='publication-version-') as temporary:
            directory = Path(temporary)
            self.approved_metadata(directory)
            report = directory / 'publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', report], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            receipt = json.loads(report.read_text())
            self.assertEqual(receipt['operations'], [])
            self.assertIn('numeric', receipt['error'].lower())

    def test_a_successful_pull_request_run_cannot_supply_publication_artifacts(self):
        with tempfile.TemporaryDirectory(prefix='publication-origin-') as temporary:
            directory = Path(temporary)
            fixture = directory / 'github-run.json'
            fixture.write_text(json.dumps({'id': 123, 'run_attempt': 1,
                'status': 'completed', 'conclusion': 'success', 'event': 'pull_request',
                'head_branch': 'feature', 'head_sha': '1' * 40,
                'path': '.github/workflows/checks.yml', 'name': 'Checks',
                'head_repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'},
                'repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'}}))
            # The external GitHub CLI boundary returns a provider response;
            # publication code and its validation are never replaced.
            gh = directory / 'gh'
            gh.write_text('#!' + sys.executable + '\nimport os\nfrom pathlib import Path\n'
                          'print(Path(os.environ["GITHUB_RUN_FIXTURE"]).read_text())\n')
            gh.chmod(0o755)
            output = directory / 'download'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'fetch',
                                     '--run-id', '123', '--directory', output],
                                    env=dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH'],
                                             GITHUB_RUN_FIXTURE=str(fixture)),
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('successful checks run on main', result.stderr.lower())
            self.assertFalse(output.exists())

    def test_fetch_downloads_only_the_approved_main_attempt_and_records_its_origin(self):
        with tempfile.TemporaryDirectory(prefix='publication-fetch-') as temporary:
            directory = Path(temporary)
            fixtures = directory / 'fixtures'
            candidate, _, _ = self.approved_metadata(fixtures)
            for image in candidate['images']:
                image['archive'] = 'webtop-arch-kde-' + image['variant'] + '.oci.tar'
                content = ('transport fixture: ' + image['variant']).encode()
                (fixtures / image['archive']).write_bytes(content)
                image['archiveSha256'] = hashlib.sha256(content).hexdigest()
            (fixtures / 'candidate.json').write_text(json.dumps(candidate))
            provider_run = {'id': 123, 'run_attempt': 2, 'run_number': 40, 'status': 'completed', 'conclusion': 'success',
                'event': 'schedule', 'head_branch': 'main', 'head_sha': candidate['revision'],
                'path': '.github/workflows/checks.yml', 'name': 'Checks',
                'head_repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'},
                'repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'}}
            (fixtures / 'run.json').write_text(json.dumps(provider_run))
            (fixtures / 'artifacts.json').write_text(json.dumps({'artifacts': [
                {'id': i, 'expired': False, 'name': name + '-123-2'} for i, name in enumerate(
                    ('candidate-results', 'webtop-arch-kde-base', 'webtop-arch-kde-salesforce'), 1)]}))
            gh = directory / 'gh'
            gh.write_text('#!' + sys.executable + '''
import json, os, shutil, sys
from pathlib import Path
root = Path(os.environ['GITHUB_FIXTURES'])
arguments = sys.argv[1:]
with (root / 'calls.jsonl').open('a') as log:
    log.write(json.dumps(arguments) + '\\n')
if arguments[0] == 'api':
    if 'workflows/checks.yml/runs' in arguments[1]:
        print(json.dumps({'workflow_runs': [json.loads((root / 'run.json').read_text())]}))
    else:
        print((root / ('artifacts.json' if '/artifacts' in arguments[1] else 'run.json')).read_text())
elif arguments[:2] == ['run', 'download']:
    name = arguments[arguments.index('--name') + 1]
    target = Path(arguments[arguments.index('--dir') + 1])
    target.mkdir(parents=True, exist_ok=True)
    if name == 'candidate-results-123-2':
        shutil.copyfile(root / 'candidate.json', target / 'candidate.json')
        shutil.copytree(root / 'validation', target / 'validation')
    else:
        archive = name.removesuffix('-123-2') + '.oci.tar'
        shutil.copyfile(root / archive, target / archive)
else:
    sys.exit(2)
''')
            gh.chmod(0o755)
            output = directory / 'download'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'fetch',
                                     '--run-id', '123', '--directory', output],
                                    env=dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH'],
                                             GITHUB_FIXTURES=str(fixtures)), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads((output / 'candidate.json').read_text()), candidate)
            source = json.loads((output / 'source.json').read_text())
            self.assertEqual((source['runId'], source['runAttempt'], source['revision']), (123, 2, candidate['revision']))
            self.assertEqual(source['artifactIds'], [1, 2, 3])
            calls = [json.loads(line) for line in (fixtures / 'calls.jsonl').read_text().splitlines()]
            downloads = [call for call in calls if call[:2] == ['run', 'download']]
            self.assertEqual(len(downloads), 3)
            self.assertTrue(all(call[call.index('--repo') + 1] == 'Electivus/webtop-arch-kde-workstation' for call in downloads))
            for image in candidate['images']:
                self.assertEqual(hashlib.sha256((output / image['archive']).read_bytes()).hexdigest(), image['archiveSha256'])

    def test_an_older_approved_run_cannot_regress_stable_after_a_newer_approval(self):
        with tempfile.TemporaryDirectory(prefix='publication-order-') as temporary:
            directory = Path(temporary)
            revision = run('git', 'rev-parse', 'HEAD').strip()
            provider_run = {'id': 123, 'run_attempt': 1, 'run_number': 40,
                'status': 'completed', 'conclusion': 'success', 'event': 'schedule',
                'head_branch': 'main', 'head_sha': revision, 'path': '.github/workflows/checks.yml', 'name': 'Checks',
                'head_repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'},
                'repository': {'full_name': 'Electivus/webtop-arch-kde-workstation'}}
            (directory / 'run.json').write_text(json.dumps(provider_run))
            (directory / 'newer.json').write_text(json.dumps({'workflow_runs': [dict(provider_run, id=124, run_number=41)]}))
            gh = directory / 'gh'
            gh.write_text('#!' + sys.executable + '\nimport os, sys\nfrom pathlib import Path\n'
                'root=Path(os.environ["GITHUB_FIXTURES"])\n'
                'print((root/("newer.json" if "workflows/checks.yml/runs" in sys.argv[2] else "run.json")).read_text())\n')
            gh.chmod(0o755)
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'fetch',
                                     '--run-id', '123', '--directory', directory / 'download'],
                                    env=dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH'],
                                             GITHUB_FIXTURES=str(directory)), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('newer approved run', result.stderr.lower())
            self.assertFalse((directory / 'download').exists())

    def test_the_approved_pair_is_published_without_changing_its_digests(self):
        with self.registry_pair() as (directory, candidate, registry, environment):
            report = directory / 'publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', report, '--registry', registry],
                                    env=environment, capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(report.read_text())
            self.assertTrue(receipt['complete'])
            self.assertEqual(receipt['state'], 'published')
            for image in candidate['images']:
                repository = image['reference'].split(':')[0]
                for tag in (candidate['version'], 'stable'):
                    request = urllib.request.Request('http://' + registry + '/v2/' + repository + '/manifests/' + tag,
                        headers={'Accept': 'application/vnd.oci.image.index.v1+json'})
                    with urllib.request.urlopen(request) as response:
                        self.assertEqual('sha256:' + hashlib.sha256(response.read()).hexdigest(), image['digest'])

    def test_an_existing_fixed_version_cannot_be_overwritten(self):
        with self.registry_pair() as (directory, candidate, registry, environment):
            # Another artifact already occupies the base version on the registry.
            occupied = registry + '/' + candidate['images'][0]['reference']
            run('docker', 'tag', candidate['images'][1]['digest'], occupied, env=environment)
            run('docker', 'push', '--quiet', occupied, env=environment)
            report = directory / 'publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', report, '--registry', registry],
                                    env=environment, capture_output=True, text=True, timeout=300)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(report.read_text())
            self.assertEqual(receipt['state'], 'rejected')
            self.assertFalse(receipt['complete'])
            self.assertEqual(receipt['operations'], [])
            self.assertIn('fixed version', receipt['error'].lower())
            request = urllib.request.Request('http://' + registry + '/v2/electivus/webtop-arch-kde-base/manifests/' + candidate['version'],
                headers={'Accept': 'application/vnd.oci.image.index.v1+json'})
            with urllib.request.urlopen(request) as response:
                self.assertEqual('sha256:' + hashlib.sha256(response.read()).hexdigest(), candidate['images'][1]['digest'])

    def test_partial_promotion_remains_incomplete_and_can_resume_the_same_artifacts(self):
        with self.registry_pair() as (directory, candidate, registry, environment):
            commands = directory / 'cli'
            commands.mkdir()
            real_docker = shutil.which('docker')
            wrapper = commands / 'docker'
            wrapper.write_text('#!' + sys.executable + '\nimport os, sys\n'
                'if sys.argv[1:3] == ["push", "--quiet"] and sys.argv[-1].endswith("/webtop-arch-kde-salesforce:stable"):\n'
                '    print("Simulated registry service interruption", file=sys.stderr)\n    sys.exit(9)\n'
                'os.execv(' + repr(real_docker) + ', [' + repr(real_docker) + '] + sys.argv[1:])\n')
            wrapper.chmod(0o755)
            first_report = directory / 'first-publication.json'
            result = subprocess.run([sys.executable, ROOT / 'scripts/publish.py', 'publish',
                                     '--directory', directory, '--report', first_report, '--registry', registry],
                                    env=dict(environment, PATH=str(commands) + os.pathsep + environment['PATH']),
                                    capture_output=True, text=True, timeout=300)
            self.assertNotEqual(result.returncode, 0)
            first = json.loads(first_report.read_text())
            self.assertFalse(first['complete'])
            self.assertEqual(first['state'], 'partially-published')
            self.assertEqual([op['state'] for op in first['operations']], ['verified'] * 3 + ['pushing'])
            resumed_report = directory / 'resumed-publication.json'
            run(sys.executable, ROOT / 'scripts/publish.py', 'publish', '--directory', directory,
                '--report', resumed_report, '--registry', registry, env=environment)
            resumed = json.loads(resumed_report.read_text())
            self.assertTrue(resumed['complete'])
            self.assertEqual(resumed['state'], 'published')
            self.assertEqual([op['reused'] for op in resumed['operations']], [True, True, True, False])
            self.assertEqual(json.loads(first_report.read_text()), first, 'Previous failure evidence must remain available')

    def test_consumer_bundle_keeps_the_tested_commands_and_digest_based_installation(self):
        with self.registry_pair() as (directory, candidate, registry, environment):
            report = directory / 'publication.json'
            run(sys.executable, ROOT / 'scripts/publish.py', 'publish', '--directory', directory,
                '--report', report, '--registry', registry, env=environment)
            output = directory / 'release'
            run(sys.executable, ROOT / 'scripts/publish.py', 'bundle', '--directory', directory,
                '--report', report, '--output', output, env=environment)
            archive_path = output / ('workstation-' + candidate['version'] + '-windows.zip')
            with zipfile.ZipFile(archive_path) as archive:
                for name, digest in candidate['commands'].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                for name in ('verify-target.cmd', 'verify-target.py', 'docs/hyperv-verification.md'):
                    source = 'distribution/windows/' + name if '/' not in name else name
                    self.assertEqual(archive.read(name), subprocess.check_output(
                        ['git', 'show', candidate['revision'] + ':' + source], cwd=ROOT))
                guide = archive.read('START-HERE.md').decode()
                self.assertIn(candidate['images'][1]['digest'], guide)
                self.assertIn('workstation.cmd install', guide)
                self.assertIn('pendente', guide)
            checksums = dict(line.split('  ', 1)[::-1] for line in (output / 'SHA256SUMS').read_text().splitlines())
            for name, digest in checksums.items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def test_interrupted_release_asset_upload_resumes_before_making_the_release_public(self):
        with tempfile.TemporaryDirectory(prefix='publication-release-') as temporary:
            directory = Path(temporary)
            assets = directory / 'assets'
            assets.mkdir()
            version = '1.0.0'
            revision = run('git', 'rev-parse', 'HEAD').strip()
            (assets / 'candidate.json').write_text(json.dumps({'version': version, 'revision': revision}))
            (assets / 'publication.json').write_text(json.dumps({'state': 'published', 'complete': True,
                'version': version, 'revision': revision, 'registry': 'docker.io'}))
            (assets / 'START-HERE.md').write_text('Public CMD guide')
            (assets / 'workstation-1.0.0-windows.zip').write_bytes(b'consumer archive fixture')
            (assets / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n'
                                                    for path in sorted(assets.iterdir())))
            provider = directory / 'provider'
            provider.mkdir()
            (provider / 'tag.json').write_text(json.dumps({'type': 'commit', 'sha': '0' * 40}))
            gh = directory / 'gh'
            gh.write_text('#!' + sys.executable + '''
import json, os, shutil, sys
from pathlib import Path
root=Path(os.environ['GITHUB_RELEASE_FIXTURE'])
args=sys.argv[1:]
state=root/'state.json'
if args[0]=='api':
    if args[1].endswith('/git/refs'):
        data=json.load(sys.stdin)
        (root/'tag.json').write_text(json.dumps({'type':'commit','sha':data['sha']}))
    if not (root/'tag.json').exists():
        print(json.dumps({'status':'404','message':'Not Found'})); sys.exit(1)
    print(json.dumps({'object':json.loads((root/'tag.json').read_text())}))
    sys.exit(0)
assert args[0]=='release' and args[args.index('--repo')+1]=='Electivus/webtop-arch-kde-workstation'
operation=args[1]
if operation=='view':
    if not state.exists(): sys.exit(1)
    print(state.read_text())
elif operation=='create':
    assert '--draft' in args
    state.write_text(json.dumps({'isDraft':True,'assets':[], 'tagName':args[2],
        'targetCommitish':args[args.index('--target')+1]}))
elif operation=='upload':
    asset=Path(args[3])
    if asset.suffix=='.zip' and (root/'fail-once').exists():
        (root/'fail-once').unlink()
        sys.exit(9)
    shutil.copyfile(asset,root/asset.name)
    value=json.loads(state.read_text()); value['assets'].append({'name':asset.name})
    state.write_text(json.dumps(value))
elif operation=='download':
    target=Path(args[args.index('--dir')+1]); target.mkdir(parents=True,exist_ok=True)
    name=args[args.index('--pattern')+1]
    shutil.copyfile(root/name,target/name)
elif operation=='edit':
    assert '--draft=false' in args
    value=json.loads(state.read_text()); value['isDraft']=False
    state.write_text(json.dumps(value))
else: sys.exit(2)
''')
            gh.chmod(0o755)
            environment = dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH'],
                               GITHUB_RELEASE_FIXTURE=str(provider))
            command = [sys.executable, ROOT / 'scripts/publish.py', 'release', '--assets', assets]
            conflicting = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertNotEqual(conflicting.returncode, 0)
            state = provider / 'state.json'
            self.assertTrue(not state.exists() or json.loads(state.read_text())['isDraft'],
                            'A conflicting Git tag must be rejected before the release becomes public')
            self.assertIn('tag', conflicting.stderr.lower())
            # Reset only this synthetic provider to exercise a fresh draft and retry.
            for path in provider.iterdir():
                path.unlink()
            (provider / 'fail-once').touch()
            interrupted = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertTrue((provider / 'state.json').exists(), interrupted.stdout + interrupted.stderr)
            self.assertTrue(json.loads((provider / 'state.json').read_text())['isDraft'])
            run(*command, env=environment)
            self.assertFalse(json.loads((provider / 'state.json').read_text())['isDraft'])
            run(*command, env=environment)
            for asset in assets.iterdir():
                self.assertEqual((provider / asset.name).read_bytes(), asset.read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
