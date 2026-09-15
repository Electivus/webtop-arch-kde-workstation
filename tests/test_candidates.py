"""Candidate transport uses real OCI archives and the Docker image store."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    process = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if process.returncode:
        raise AssertionError(process.stderr or process.stdout)
    return process.stdout


class CandidateAcceptance(unittest.TestCase):
    def test_builder_uses_one_clean_source_for_the_coordinated_pair(self):
        version = 'build-probe-' + uuid.uuid4().hex[:10]
        tags = [f'electivus/webtop-arch-kde-{variant}:{version}' for variant in ('base', 'salesforce')]
        with tempfile.TemporaryDirectory(prefix='candidate-source-', dir=ROOT / '.local') as directory:
            fixture = Path(directory)
            source = fixture / 'source'
            bundle = fixture / 'bundle'
            run('git', 'clone', '--quiet', '--no-hardlinks', ROOT, source)
            base = source / 'images/base/Dockerfile'
            compiler = base.read_text(encoding='utf-8').split('FROM lscr.io/')[0]
            base.write_text(compiler + '''FROM scratch
ARG VERSION
ARG REVISION
LABEL org.opencontainers.image.version="${VERSION}" org.opencontainers.image.revision="${REVISION}" io.electivus.workstation.variant="base"
COPY --from=commands /out/ /opt/electivus/windows/
''', encoding='utf-8')
            (source / 'images/salesforce/Dockerfile').write_text('''ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG BASE_DIGEST
LABEL io.electivus.workstation.variant="salesforce" org.opencontainers.image.base.name="${BASE_IMAGE}" org.opencontainers.image.base.digest="${BASE_DIGEST}"
''', encoding='utf-8')
            run('git', '-C', source, 'add', 'images/base/Dockerfile', 'images/salesforce/Dockerfile')
            run('git', '-C', source, '-c', 'user.name=Workstation fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '--quiet', '-m', 'Create an isolated candidate transport fixture')
            revision = run('git', '-C', source, 'rev-parse', 'HEAD').strip()
            try:
                produced = json.loads(run(sys.executable, 'scripts/candidate.py', 'build', '--source', source,
                                          '--directory', bundle, '--version', version, '--revision', revision))
                self.assertEqual(produced['state'], 'built')
                self.assertEqual(produced['revision'], revision)
                self.assertEqual(produced['version'], version)
                self.assertEqual(produced['images'][1]['baseDigest'], produced['images'][0]['digest'])
                self.assertTrue((bundle / 'commands' / 'workstation.exe').is_file())
                self.assertTrue((bundle / 'commands' / 'workstation').is_file())
                self.assertEqual(json.loads((bundle / 'build.json').read_text(encoding='utf-8'))['state'], 'built')
                controller = (bundle / 'commands/workstation.exe').read_bytes()
                command_directory = (bundle / 'commands').resolve()
                self.assertTrue(command_directory.is_relative_to(fixture.resolve()))
                shutil.rmtree(command_directory)
                run(sys.executable, 'scripts/candidate.py', 'load', '--directory', bundle)
                self.assertEqual((bundle / 'commands/workstation.exe').read_bytes(), controller)
                rejected = subprocess.run([sys.executable, 'scripts/candidate.py', 'test', '--directory', str(bundle),
                                           '--prove-test-failure'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(rejected.returncode, 0)
                validation = json.loads((bundle / 'validation/validation.json').read_text(encoding='utf-8'))
                self.assertFalse(validation['approved'])
                self.assertTrue(validation['failureProof'])
                self.assertEqual(hashlib.sha256((bundle / 'commands/workstation.exe').read_bytes()).hexdigest(),
                                 produced['commands']['workstation.exe'])
                changed_source = source / 'cmd/workstation/main.go'
                changed_source.write_bytes(changed_source.read_bytes() + b'\n// Uncommitted fixture change.\n')
                dirty_output = fixture / 'dirty-output'
                dirty = subprocess.run([sys.executable, 'scripts/candidate.py', 'build', '--source', str(source),
                                        '--directory', str(dirty_output), '--version', version, '--revision', revision],
                                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(dirty.returncode, 0)
                self.assertIn('Uncommitted source', json.loads((dirty_output / 'build.json').read_text(encoding='utf-8'))['error'])
                self.assertFalse((dirty_output / 'candidate.json').exists())
                run('docker', 'image', 'rm', '--force', *reversed(tags))
                with (bundle / 'commands.tar').open('ab') as damaged:
                    damaged.write(b'corrupt transport')
                corrupt = subprocess.run([sys.executable, 'scripts/candidate.py', 'load', '--directory', str(bundle)],
                                         cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(corrupt.returncode, 0)
                self.assertIn('Controller archive checksum mismatch', corrupt.stderr)
                for reference in tags:
                    self.assertNotEqual(subprocess.run(['docker', 'image', 'inspect', reference], capture_output=True).returncode, 0)
            finally:
                subprocess.run(['docker', 'image', 'rm', '--force', *reversed(tags)], capture_output=True)

    def test_candidate_identifies_the_exact_oci_pair_and_its_base_relationship(self):
        version = 'probe-' + uuid.uuid4().hex[:10]
        revision = run('git', 'rev-parse', 'HEAD').strip()
        tags = [f'electivus/webtop-arch-kde-{variant}:{version}' for variant in ('base', 'salesforce')]
        with tempfile.TemporaryDirectory(prefix='candidate-', dir=ROOT / '.local') as directory:
            fixture = Path(directory)
            (fixture / 'marker').write_text(version, encoding='utf-8')
            (fixture / 'base.Dockerfile').write_text('''FROM scratch
ARG VERSION
ARG REVISION
LABEL org.opencontainers.image.version="${VERSION}" org.opencontainers.image.revision="${REVISION}" io.electivus.workstation.variant="base"
COPY marker /marker
''', encoding='utf-8')
            (fixture / 'salesforce.Dockerfile').write_text('''ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG BASE_DIGEST
LABEL io.electivus.workstation.variant="salesforce" org.opencontainers.image.base.name="${BASE_IMAGE}" org.opencontainers.image.base.digest="${BASE_DIGEST}"
COPY marker /salesforce-marker
''', encoding='utf-8')
            digests = []
            try:
                for index, variant in enumerate(('base', 'salesforce')):
                    archive = fixture / f'webtop-arch-kde-{variant}.oci.tar'
                    args = ['docker', 'buildx', 'build', '--platform', 'linux/amd64', '--provenance=mode=min',
                            '--file', fixture / f'{variant}.Dockerfile', '--tag', tags[index],
                            '--output', f'type=oci,dest={archive}', '--build-arg', 'VERSION=' + version,
                            '--build-arg', 'REVISION=' + revision]
                    if index:
                        args += ['--build-arg', 'BASE_IMAGE=' + tags[0], '--build-arg', 'BASE_DIGEST=' + digests[0]]
                    run(*args, fixture)
                    run('docker', 'load', '--input', archive)
                    digests.append(json.loads(run('docker', 'image', 'inspect', tags[index]))[0]['Id'])
                result = run(sys.executable, 'scripts/candidate.py', 'record', '--directory', fixture,
                             '--version', version, '--revision', revision)
                candidate = json.loads(result)
                self.assertEqual(candidate['state'], 'built')
                self.assertEqual(candidate['version'], version)
                self.assertEqual(candidate['revision'], revision)
                self.assertEqual(candidate['architecture'], 'linux/amd64')
                self.assertEqual([item['digest'] for item in candidate['images']], digests)
                self.assertEqual(candidate['images'][1]['baseDigest'], digests[0])
                for item in candidate['images']:
                    self.assertEqual(item['archiveSha256'], hashlib.sha256((fixture / item['archive']).read_bytes()).hexdigest())
                self.assertEqual(json.loads((fixture / 'candidate.json').read_text(encoding='utf-8')), candidate)
                run('docker', 'image', 'rm', '--force', *reversed(tags))
                imported = json.loads(run(sys.executable, 'scripts/candidate.py', 'load', '--directory', fixture))
                self.assertEqual(imported['state'], 'loaded')
                self.assertEqual([item['digest'] for item in imported['images']], digests)
                for reference, digest in zip(tags, digests):
                    self.assertEqual(json.loads(run('docker', 'image', 'inspect', reference))[0]['Id'], digest)
                # These transport-only images deliberately lack the workstation
                # and its delivered commands. The real acceptance must reject them.
                rejected = subprocess.run([sys.executable, 'scripts/candidate.py', 'test', '--directory', str(fixture)],
                                          cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(rejected.returncode, 0)
                validation = json.loads((fixture / 'validation' / 'validation.json').read_text(encoding='utf-8'))
                self.assertEqual(validation['state'], 'failed')
                self.assertFalse(validation['approved'])
                self.assertEqual(validation['digests'], digests)
                checks = json.loads((fixture / 'validation' / 'checks' / 'acceptance.json').read_text(encoding='utf-8'))
                self.assertEqual(checks['checks'][0]['state'], 'failed')
                self.assertIn('FAILED', (fixture / 'validation' / 'checks' / 'commands.log').read_text(encoding='utf-8'))
            finally:
                subprocess.run(['docker', 'image', 'rm', '--force', *reversed(tags)], capture_output=True)


if __name__ == '__main__':
    (ROOT / '.local').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
