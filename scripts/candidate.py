#!/usr/bin/env python3
"""Identify and transport the exact pair of workstation candidate archives."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_blob(archive, descriptor):
    digest = descriptor['digest']
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Unsupported OCI content digest')
    member = archive.getmember('blobs/sha256/' + digest.removeprefix('sha256:'))
    if not member.isfile() or member.size != descriptor['size'] or member.size > 16 * 1024 * 1024:
        raise ValueError('Invalid OCI metadata size')
    raw = archive.extractfile(member).read()
    if 'sha256:' + hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('OCI metadata checksum mismatch')
    return json.loads(raw)


def image_metadata(path):
    with tarfile.open(path, 'r:') as archive:
        index = json.load(archive.extractfile('index.json'))
        if len(index['manifests']) != 1:
            raise ValueError('A candidate archive must contain exactly one named image')
        descriptor = index['manifests'][0]
        manifest = read_blob(archive, descriptor)
        if 'manifests' in manifest:
            choices = [entry for entry in manifest['manifests']
                       if entry.get('platform', {}).get('os') == 'linux'
                       and entry.get('platform', {}).get('architecture') == 'amd64']
            if len(choices) != 1:
                raise ValueError('A candidate must contain exactly one linux/amd64 image')
            manifest = read_blob(archive, choices[0])
        configuration = read_blob(archive, manifest['config'])
        if (configuration['os'], configuration['architecture']) != ('linux', 'amd64'):
            raise ValueError('Candidate architecture must be linux/amd64')
        return descriptor['digest'], configuration


def record(args):
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', args.version):
        raise ValueError('Invalid candidate version')
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision):
        raise ValueError('The candidate revision must be an exact Git commit')
    candidate = {'schemaVersion': 1, 'state': 'built', 'version': args.version,
                 'revision': args.revision, 'architecture': 'linux/amd64', 'images': []}
    configurations = []
    for variant in ('base', 'salesforce'):
        archive = args.directory / f'webtop-arch-kde-{variant}.oci.tar'
        digest, configuration = image_metadata(archive)
        labels = configuration['config']['Labels']
        if (labels.get('org.opencontainers.image.version'), labels.get('org.opencontainers.image.revision'),
                labels.get('io.electivus.workstation.variant')) != (args.version, args.revision, variant):
            raise ValueError('Candidate version, revision or variant does not match its archive')
        reference = f'electivus/webtop-arch-kde-{variant}:{args.version}'
        loaded = json.loads(subprocess.check_output(['docker', 'image', 'inspect', reference], text=True))[0]
        if loaded['Id'] != digest:
            raise ValueError('The loaded image must preserve the OCI archive digest; use the containerd image store')
        image = {'variant': variant, 'reference': reference, 'digest': digest,
                 'archive': archive.name, 'archiveSha256': sha256_file(archive), 'archiveBytes': archive.stat().st_size}
        if variant == 'salesforce':
            base = candidate['images'][0]
            base_layers = configurations[0]['rootfs']['diff_ids']
            if (labels.get('org.opencontainers.image.base.digest') != base['digest']
                    or labels.get('org.opencontainers.image.base.name') != base['reference']
                    or configuration['rootfs']['diff_ids'][:len(base_layers)] != base_layers):
                raise ValueError('Salesforce must derive from the matching base candidate')
            image['baseDigest'] = base['digest']
        candidate['images'].append(image)
        configurations.append(configuration)
    with (args.directory / 'candidate.json').open('x', encoding='utf-8') as output:
        commands = args.directory / 'commands'
        if commands.is_dir():
            candidate['commands'] = {file.relative_to(commands).as_posix(): sha256_file(file)
                                     for file in sorted(commands.rglob('*')) if file.is_file()}
            candidate['commandsArchive'] = 'commands.tar'
            candidate['commandsArchiveSha256'] = sha256_file(args.directory / 'commands.tar')
        output.write(json.dumps(candidate, indent=2) + '\n')
    return candidate


def load(args):
    candidate = json.loads((args.directory / 'candidate.json').read_text(encoding='utf-8'))
    if candidate.get('schemaVersion') != 1 or len(candidate.get('images', [])) != 2:
        raise ValueError('Invalid candidate manifest')
    for expected_variant, image in zip(('base', 'salesforce'), candidate['images']):
        expected_archive = f'webtop-arch-kde-{expected_variant}.oci.tar'
        if image['archive'] != expected_archive or image['variant'] != expected_variant:
            raise ValueError('Candidate archive and variant must match the coordinated pair')
        archive = args.directory / expected_archive
        if sha256_file(archive) != image['archiveSha256']:
            raise ValueError('Candidate archive checksum mismatch: ' + expected_archive)
        digest, configuration = image_metadata(archive)
        if digest != image['digest']:
            raise ValueError('The archive no longer matches the candidate digest')
        labels = configuration['config']['Labels']
        if (labels.get('org.opencontainers.image.version'), labels.get('org.opencontainers.image.revision'),
                labels.get('io.electivus.workstation.variant')) != (candidate['version'], candidate['revision'], expected_variant):
            raise ValueError('The archive no longer matches the candidate version, code or variant')
    if 'commands' in candidate:
        if candidate.get('commandsArchive') != 'commands.tar':
            raise ValueError('Invalid controller archive name')
        controller_archive = args.directory / 'commands.tar'
        if sha256_file(controller_archive) != candidate['commandsArchiveSha256']:
            raise ValueError('Controller archive checksum mismatch')
        expected = {}
        directories = {'commands'}
        for name, checksum in candidate['commands'].items():
            relative = PurePosixPath(name)
            if (relative.is_absolute() or '..' in relative.parts or not relative.parts
                    or any(character in name for character in ('\\', ':', '\0'))):
                raise ValueError('Invalid controller file path')
            full_name = PurePosixPath('commands') / relative
            expected[full_name.as_posix()] = checksum
            directories.update(parent.as_posix() for parent in full_name.parents if parent != PurePosixPath('.'))
        with tarfile.open(controller_archive, 'r:') as archive:
            seen = set()
            for member in archive:
                if member.isdir() and member.name in directories:
                    continue
                if not member.isfile() or member.name not in expected or member.name in seen:
                    raise ValueError('Unexpected file in the controller archive')
                if hashlib.file_digest(archive.extractfile(member), 'sha256').hexdigest() != expected[member.name]:
                    raise ValueError('Controller file checksum mismatch')
                seen.add(member.name)
            if seen != set(expected):
                raise ValueError('The controller archive is incomplete')
            commands = args.directory / 'commands'
            if not commands.exists():
                archive.extractall(args.directory, filter='data')
        for name, checksum in candidate['commands'].items():
            file = args.directory / 'commands' / name
            if file.is_symlink() or sha256_file(file) != checksum:
                raise ValueError('The extracted controller differs from the candidate: ' + name)
    # Verify both archives before loading either, so damaged transport cannot
    # partially replace the selected pair in the local image store.
    for image in candidate['images']:
        subprocess.run(['docker', 'load', '--input', str(args.directory / image['archive'])],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        actual = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image['reference']], text=True))[0]
        if actual['Id'] != image['digest']:
            raise ValueError('The imported image did not preserve the candidate digest')
    return dict(candidate, state='loaded')


def test_candidate(args):
    candidate = json.loads((args.directory / 'candidate.json').read_text(encoding='utf-8'))
    output = args.output or args.directory / 'validation'
    output.mkdir(parents=True, exist_ok=False)
    report = {'schemaVersion': 1, 'state': 'running', 'approved': False,
              'version': candidate['version'], 'revision': candidate['revision'],
              'digests': [image['digest'] for image in candidate['images']],
              'failureProof': args.prove_test_failure}
    report_path = output / 'validation.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    try:
        load(args)
        environment = dict(os.environ,
                           WORKSTATION_TEST_IMAGE=candidate['images'][0]['reference'],
                           WORKSTATION_SALESFORCE_TEST_IMAGE=candidate['images'][1]['reference'],
                           WORKSTATION_TEST_CLI=str((args.directory / 'commands' /
                                                   ('workstation.cmd' if os.name == 'nt' else 'workstation')).resolve()))
        if args.prove_test_failure:
            environment['WORKSTATION_TEST_CLI'] = str((args.directory / 'missing-controller-for-failure-proof').resolve())
        with (output / 'runner.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, str(ROOT / 'scripts/acceptance.py'),
                                        '--output', str(output / 'checks')], cwd=ROOT, env=environment,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end='', file=sys.stderr, flush=True)
            process.wait()
        checks = json.loads((output / 'checks' / 'acceptance.json').read_text(encoding='utf-8'))
        contract = ROOT / 'tests/acceptance.json'
        required = json.loads(contract.read_text(encoding='utf-8'))['checks']
        if (process.returncode != 0 or checks.get('state') != 'passed'
                or checks.get('contractSha256') != sha256_file(contract)
                or [check['id'] for check in checks['checks']] != [check['id'] for check in required]
                or any(check['state'] != 'passed' for check in checks['checks'])):
            raise ValueError('The required acceptance contract did not pass; inspect checks/acceptance.json and its logs')
        for image in candidate['images']:
            actual = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image['reference']], text=True))[0]
            if actual['Id'] != image['digest']:
                raise ValueError('A candidate image changed during acceptance')
        if args.prove_test_failure:
            raise ValueError('A deliberate failure proof cannot approve a candidate')
        report.update(state='passed', approved=True, contractSha256=checks['contractSha256'])
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        report.update(state='failed', error=str(error))
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def build(args):
    args.directory = args.directory.resolve()
    source = args.source.resolve()
    args.directory.mkdir(parents=True, exist_ok=False)
    report = {'schemaVersion': 1, 'state': 'building', 'stage': 'source',
              'version': args.version, 'revision': args.revision}
    report_path = args.directory / 'build.json'

    def step(name, command):
        report['stage'] = name
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print('Candidate stage: ' + name, file=sys.stderr, flush=True)
        with (args.directory / (name + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run(list(map(str, command)), check=True, stdout=log, stderr=subprocess.STDOUT, timeout=3600)

    try:
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', args.version):
            raise ValueError('Invalid candidate version')
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        if not re.fullmatch(r'[0-9a-f]{40}', args.revision) or head != args.revision:
            raise ValueError('The candidate must be built from the exact requested Git commit')
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
        if dirty:
            raise ValueError('Uncommitted source changes cannot be identified as a candidate Git revision')
        commands = args.directory / 'commands'
        step('commands', ['docker', 'buildx', 'build', '--file', source / 'images/base/Dockerfile',
                          '--target', 'commands-export', '--output', f'type=local,dest={commands}', source])
        with tarfile.open(args.directory / 'commands.tar', 'w') as archive:
            archive.add(commands, arcname='commands')
        base_digest = None
        for variant in ('base', 'salesforce'):
            reference = f'electivus/webtop-arch-kde-{variant}:{args.version}'
            archive = args.directory / f'webtop-arch-kde-{variant}.oci.tar'
            command = ['docker', 'buildx', 'build', '--platform', 'linux/amd64', '--provenance=mode=min',
                       '--file', source / f'images/{variant}/Dockerfile', '--tag', reference,
                       '--build-arg', 'VERSION=' + args.version, '--build-arg', 'REVISION=' + args.revision,
                       '--output', f'type=oci,dest={archive}']
            if args.corporate_ca:
                command += ['--secret', 'id=corporate_ca,src=' + str(args.corporate_ca.resolve())]
            if variant == 'salesforce':
                command += ['--build-arg', f'BASE_IMAGE=electivus/webtop-arch-kde-base:{args.version}',
                            '--build-arg', 'BASE_DIGEST=' + base_digest]
            step('build-' + variant, [*command, source])
            step('load-' + variant, ['docker', 'load', '--input', archive])
            if variant == 'base':
                base_digest = image_metadata(archive)[0]
        # The downloadable Windows controller must be the one embedded in the image.
        name = 'ew-candidate-bundle-' + uuid.uuid4().hex[:10]
        container = subprocess.check_output(['docker', 'create', '--name', name, '--entrypoint', '/unused',
                                             f'electivus/webtop-arch-kde-base:{args.version}'], text=True).strip()
        try:
            payload = subprocess.check_output(['docker', 'cp', container + ':/opt/electivus/windows/workstation.exe', '-'])
            with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
                binary = archive.extractfile('workstation.exe').read()
            if hashlib.sha256(binary).hexdigest() != sha256_file(commands / 'workstation.exe'):
                raise ValueError('The distributed command differs from the candidate image')
        finally:
            subprocess.run(['docker', 'container', 'rm', '--volumes', container], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        candidate = record(args)
        report.update(state='built', stage='complete')
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return candidate
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        report.update(state='failed', error=str(error))
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    recorder = commands.add_parser('record', help='Record the built, loaded OCI pair before acceptance')
    recorder.add_argument('--directory', type=Path, required=True)
    recorder.add_argument('--version', required=True)
    recorder.add_argument('--revision', required=True)
    loader = commands.add_parser('load', help='Verify and import the recorded OCI pair')
    loader.add_argument('--directory', type=Path, required=True)
    tester = commands.add_parser('test', help='Run the complete acceptance contract against the recorded pair')
    tester.add_argument('--directory', type=Path, required=True)
    tester.add_argument('--output', type=Path)
    tester.add_argument('--prove-test-failure', action='store_true',
                        help='Exercise rejection with an unavailable controller; never approves or changes the archives')
    builder = commands.add_parser('build', help='Build and export both variants from one clean Git commit')
    builder.add_argument('--source', type=Path, default=ROOT)
    builder.add_argument('--directory', type=Path, required=True)
    builder.add_argument('--version', required=True)
    builder.add_argument('--revision', required=True)
    builder.add_argument('--corporate-ca', type=Path)
    args = parser.parse_args()
    result = {'record': record, 'load': load, 'test': test_candidate, 'build': build}[args.command](args)
    print(json.dumps(result, indent=2))
    return 1 if result['state'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
