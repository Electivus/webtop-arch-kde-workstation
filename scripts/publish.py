#!/usr/bin/env python3
"""Publish a coordinated pair only after its complete acceptance contract passes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import candidate as candidate_transport

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'Electivus/webtop-arch-kde-workstation'


def github_api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPOSITORY + '/' + path], text=True))


def approved_run(run_id):
    run = github_api('actions/runs/' + str(run_id))
    if (run.get('id') != run_id or run.get('status') != 'completed' or run.get('conclusion') != 'success'
            or run.get('event') not in ('push', 'schedule', 'workflow_dispatch')
            or run.get('head_branch') != 'main' or run.get('path') != '.github/workflows/checks.yml'
            or run.get('name') != 'Checks' or run.get('head_repository', {}).get('full_name') != REPOSITORY
            or run.get('repository', {}).get('full_name') != REPOSITORY
            or not re.fullmatch(r'[0-9a-f]{40}', run.get('head_sha', ''))):
        raise ValueError('Publication requires a successful Checks run on main in ' + REPOSITORY)
    recent = github_api('actions/workflows/checks.yml/runs?branch=main&status=success&per_page=100')['workflow_runs']
    if any(item['run_number'] > run['run_number'] and item.get('event') in ('push', 'schedule', 'workflow_dispatch')
           and item.get('head_repository', {}).get('full_name') == REPOSITORY for item in recent):
        raise ValueError('A newer approved run exists; do not regress stable to this older candidate')
    return run


def fetch(args):
    run = approved_run(args.run_id)
    subprocess.run(['git', 'merge-base', '--is-ancestor', run['head_sha'], 'HEAD'], cwd=ROOT, check=True)
    if args.directory.exists():
        raise ValueError('Keep the existing artifacts; select a new download directory')
    attempt = run['run_attempt']
    names = [prefix + '-' + str(args.run_id) + '-' + str(attempt)
             for prefix in ('candidate-results', 'webtop-arch-kde-base', 'webtop-arch-kde-salesforce')]
    artifacts = github_api('actions/runs/' + str(args.run_id) + '/artifacts?per_page=100')['artifacts']
    selected = []
    for name in names:
        matching = [artifact for artifact in artifacts if artifact['name'] == name and not artifact['expired']]
        if len(matching) != 1:
            raise ValueError('Exactly one unexpired artifact is required: ' + name)
        selected.append(matching[0])
    args.directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.publication-download-', dir=args.directory.parent) as temporary:
        stage = Path(temporary) / 'candidate'
        stage.mkdir()
        for index, artifact in enumerate(selected):
            subprocess.run(['gh', 'run', 'download', str(args.run_id), '--repo', REPOSITORY,
                            '--name', artifact['name'], '--dir', str(stage)], check=True)
            if index == 0:
                candidate = approved_candidate(stage)
                if candidate['revision'] != run['head_sha']:
                    raise ValueError('The downloaded candidate is not the approved run revision')
        for image in candidate['images']:
            archive = 'webtop-arch-kde-' + image['variant'] + '.oci.tar'
            if image['archive'] != archive or candidate_transport.sha256_file(stage / archive) != image['archiveSha256']:
                raise ValueError('Downloaded candidate archive checksum mismatch')
        current = approved_run(args.run_id)
        if current['run_attempt'] != attempt or current['head_sha'] != run['head_sha']:
            raise ValueError('The source run changed during download; obtain its approved attempt again')
        source = {'repository': REPOSITORY, 'runId': args.run_id, 'runAttempt': attempt,
                  'revision': run['head_sha'], 'artifactIds': [artifact['id'] for artifact in selected]}
        (stage / 'source.json').write_text(json.dumps(source, indent=2) + '\n', encoding='utf-8')
        stage.rename(args.directory)
    return source


def approved_candidate(directory):
    validation = json.loads((directory / 'validation/validation.json').read_text())
    if (validation.get('approved') is not True or validation.get('state') != 'passed'
            or validation.get('failureProof') is not False):
        raise ValueError('The candidate acceptance did not pass; publication and stable promotion are blocked')
    candidate = json.loads((directory / 'candidate.json').read_text())
    revision, version = candidate['revision'], candidate['version']
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('The candidate must identify an exact source commit')
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', version) or version in ('stable', 'latest'):
        raise ValueError('Use a fixed candidate version, not a moving alias')
    images = candidate['images']
    if (candidate.get('schemaVersion') != 1 or candidate.get('architecture') != 'linux/amd64'
            or [image['variant'] for image in images] != ['base', 'salesforce']):
        raise ValueError('The candidate must contain the coordinated linux/amd64 pair')
    for image in images:
        expected = 'electivus/webtop-arch-kde-' + image['variant'] + ':' + version
        if image['reference'] != expected or not re.fullmatch(r'sha256:[0-9a-f]{64}', image['digest']):
            raise ValueError('Unexpected publication repository, version or digest')
    if (validation['revision'] != revision or validation['validatorRevision'] != revision
            or validation['version'] != version or validation['digests'] != [image['digest'] for image in images]):
        raise ValueError('The acceptance does not identify this exact candidate pair')
    contract = subprocess.check_output(['git', 'show', revision + ':tests/acceptance.json'], cwd=ROOT)
    checks = json.loads((directory / 'validation/checks/acceptance.json').read_text())
    digest = hashlib.sha256(contract).hexdigest()
    required = json.loads(contract)['checks']
    if (not required or checks.get('state') != 'passed'
            or checks.get('contractSha256') != digest or validation.get('contractSha256') != digest
            or [check['id'] for check in checks['checks']] != [check['id'] for check in required]
            or any(check.get('state') != 'passed' or check.get('exitCode') != 0 for check in checks['checks'])):
        raise ValueError('The complete acceptance contract must pass before any publication operation')
    return candidate


def manifest_digest(registry, repository, tag):
    headers = {'Accept': ', '.join(('application/vnd.oci.image.index.v1+json',
               'application/vnd.docker.distribution.manifest.list.v2+json',
               'application/vnd.oci.image.manifest.v1+json',
               'application/vnd.docker.distribution.manifest.v2+json'))}
    if registry == 'docker.io':
        query = urllib.parse.urlencode({'service': 'registry.docker.io', 'scope': 'repository:' + repository + ':pull'})
        with urllib.request.urlopen('https://auth.docker.io/token?' + query, timeout=30) as response:
            headers['Authorization'] = 'Bearer ' + json.load(response)['token']
        address = 'https://registry-1.docker.io'
    elif re.fullmatch(r'127\.0\.0\.1:[0-9]{1,5}', registry):
        address = 'http://' + registry
    else:
        raise ValueError('Use Docker Hub or an isolated loopback registry for verification')
    request = urllib.request.Request(address + '/v2/' + repository + '/manifests/' + tag, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError('Unexpected registry manifest size')
            digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
            if response.headers.get('Docker-Content-Digest') != digest:
                raise ValueError('The registry manifest does not match its reported digest')
            return digest
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def publish(args):
    report = {'schemaVersion': 1, 'state': 'rejected', 'complete': False, 'operations': []}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)

    def save():
        temporary = args.report.with_name(args.report.name + '.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(args.report)

    try:
        candidate = approved_candidate(args.directory)
        if args.registry == 'docker.io':
            if not candidate['version'][0].isdigit():
                raise ValueError('Docker Hub requires a numeric version prefix covered by the immutable tag policy')
            source = json.loads((args.directory / 'source.json').read_text())
            run = approved_run(source['runId'])
            if run['head_sha'] != candidate['revision'] or run['run_attempt'] != source['runAttempt']:
                raise ValueError('The source run no longer matches the approved artifacts')
        elif not re.fullmatch(r'127\.0\.0\.1:[0-9]{1,5}', args.registry):
            raise ValueError('Use Docker Hub or an isolated loopback registry for verification')
        for image in candidate['images']:
            existing = manifest_digest(args.registry, image['reference'].split(':')[0], candidate['version'])
            if existing is not None and existing != image['digest']:
                raise ValueError('The fixed version already identifies a different artifact: ' + image['reference'])
        candidate_transport.load(argparse.Namespace(directory=args.directory))
        report.update(state='publishing', version=candidate['version'], revision=candidate['revision'],
                      registry=args.registry, externalPublication=args.registry == 'docker.io')
        save()
        prefix = '' if args.registry == 'docker.io' else args.registry + '/'
        for tag in (candidate['version'], 'stable'):
            for image in candidate['images']:
                repository = image['reference'].split(':')[0]
                reference = prefix + repository + ':' + tag
                existing = manifest_digest(args.registry, repository, tag)
                if tag != 'stable' and existing is not None and existing != image['digest']:
                    raise ValueError('The fixed version changed during publication: ' + reference)
                reused = existing == image['digest']
                operation = {'reference': reference, 'digest': image['digest'],
                             'state': 'verified' if reused else 'pushing', 'reused': reused}
                report['operations'].append(operation)
                save()
                if reused:
                    continue
                subprocess.run(['docker', 'image', 'tag', image['digest'], reference], check=True, capture_output=True)
                subprocess.run(['docker', 'push', '--quiet', reference], check=True,
                               capture_output=True, text=True, timeout=1800)
                if manifest_digest(args.registry, repository, tag) != image['digest']:
                    raise ValueError('The published digest differs from the tested artifact: ' + reference)
                operation['state'] = 'verified'
                save()
        report.update(state='published', complete=True)
        save()
        return report
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        if report['operations']:
            report['state'] = 'partially-published'
        report['error'] = str(error)
        save()
        return report


def bundle(args):
    candidate = approved_candidate(args.directory)
    receipt = json.loads(args.report.read_text())
    if (receipt.get('complete') is not True or receipt.get('state') != 'published'
            or receipt.get('version') != candidate['version'] or receipt.get('revision') != candidate['revision']
            or len(receipt.get('operations', [])) != 4
            or any(operation['state'] != 'verified' for operation in receipt['operations'])):
        raise ValueError('Only a completed coordinated publication can supply a consumer bundle')
    commands = candidate['commands']
    required = {'setup.cmd', 'workstation.cmd', 'workstation.exe', 'workstation',
                'licenses/ELECTIVUS-LICENSE', 'licenses/GO-LICENSE', 'licenses/MOBY-LICENSE',
                'licenses/THIRD-PARTY.md'}
    if set(commands) != required:
        raise ValueError('The tested command bundle and its licenses must be complete')
    files = {}
    for name, digest in commands.items():
        path = args.directory / 'commands' / name
        if path.is_symlink() or candidate_transport.sha256_file(path) != digest:
            raise ValueError('The consumer command differs from its tested artifact: ' + name)
        files[name] = path.read_bytes()
    for name in ('verify-target.cmd', 'verify-target.py', 'docs/hyperv-verification.md',
                 'docs/backups.md', 'docs/image-updates.md', 'docs/application-updates.md',
                 'docs/network.md', 'docs/projects.md', 'docs/packages.md', 'docs/licensing.md', 'LICENSE'):
        source = 'distribution/windows/' + name if name.startswith('verify-target.') else name
        files[name] = subprocess.check_output(['git', 'show', candidate['revision'] + ':' + source], cwd=ROOT)
    image = candidate['images'][1]
    reference = image['reference'].split(':')[0] + '@' + image['digest']
    guide = f'''# Instalar a workstation Salesforce

Entrega `{candidate['version']}`, fonte `{candidate['revision']}`.
Esta versão passou pela aceitação local/CI. A verificação real em Hyper-V permanece **pendente**.

Extraia este ZIP pelo Explorador de Arquivos e abra o **CMD** nessa pasta.
Requer Docker Desktop com containers Linux; não requer PowerShell, WSL2 ou Python no Windows.
O backend Hyper-V e o compartilhamento de pastas precisam estar disponíveis no Docker Desktop do destino.

```bat
set "WS_IMAGE={reference}"
docker pull "%WS_IMAGE%"
setup.cmd "%WS_IMAGE%" "%LOCALAPPDATA%\\Electivus\\workstation-tools"
cd /d "%LOCALAPPDATA%\\Electivus\\workstation-tools"
workstation.cmd install --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce" --name electivus-salesforce --image "%WS_IMAGE%" --port 3001
workstation.cmd start --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce"
workstation.cmd prepare --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce"
workstation.cmd certificate --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce"
workstation.cmd trust --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce"
workstation.cmd start --profile "%LOCALAPPDATA%\\Electivus\\Workstation\\salesforce" --open-browser
```

Confira a impressão do certificado localhost antes da confirmação do Windows.
O primeiro preparo exige internet e baixa os aplicativos oficiais para seu volume pessoal.
Se a rede usa proxy ou certificados corporativos, configure a entrada opcional de [conectividade](docs/network.md) antes de iniciar.
Os padrões são 6 GiB e 4 CPUs para o container; reserve recursos também para Windows e outros containers.
Projetos ficam em `~/projects`. A [pasta de troca](docs/projects.md) exige compartilhamento no Docker Desktop.

O desktop abre em `https://localhost:3001/`, somente no próprio notebook e sem senha adicional.
Fechar a aba preserva processos; para encerrar use `workstation.cmd stop` com o mesmo argumento `--profile`.
O atalho está no diretório do perfil. Atualizações são explícitas, com [backup](docs/backups.md).

Para testar o notebook de destino, use [o roteiro Hyper-V](docs/hyperv-verification.md)
e os arquivos `verify-target.cmd` e `verify-target.py` desta entrega.
Os checks visuais e do teclado físico são registrados no destino e não são substituídos pelo CI.

`candidate.json` identifica ambos os digests, `publication.json` registra a publicação,
e `SHA256SUMS` no GitHub Release identifica os arquivos baixados.
O código Electivus usa MIT; as licenças de terceiros acompanham `licenses/`.
'''
    files['START-HERE.md'] = guide.encode()
    files['candidate.json'] = (args.directory / 'candidate.json').read_bytes()
    public_receipt = {key: receipt[key] for key in ('schemaVersion', 'state', 'complete', 'version', 'revision', 'registry')}
    public_receipt['operations'] = [{key: operation[key] for key in ('reference', 'digest', 'state')}
                                    for operation in receipt['operations']]
    files['publication.json'] = (json.dumps(public_receipt, indent=2) + '\n').encode()
    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output / ('workstation-' + candidate['version'] + '-windows.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for name, content in sorted(files.items()):
            output.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), content,
                            compress_type=zipfile.ZIP_DEFLATED)
    for name in ('candidate.json', 'publication.json', 'START-HERE.md'):
        (args.output / name).write_bytes(files[name])
    assets = sorted(args.output.iterdir())
    (args.output / 'SHA256SUMS').write_text(''.join(candidate_transport.sha256_file(path) + '  ' + path.name + '\n'
                                                   for path in assets), encoding='utf-8')
    return {'state': 'bundled', 'version': candidate['version'], 'archive': str(archive)}


def release(args):
    candidate = json.loads((args.assets / 'candidate.json').read_text())
    receipt = json.loads((args.assets / 'publication.json').read_text())
    version, revision = candidate['version'], candidate['revision']
    if (not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', version) or version in ('stable', 'latest')
            or not re.fullmatch(r'[0-9a-f]{40}', revision)
            or receipt.get('state') != 'published' or receipt.get('complete') is not True
            or receipt.get('registry') != 'docker.io' or receipt.get('version') != version
            or receipt.get('revision') != revision):
        raise ValueError('A public release requires a completed Docker Hub delivery of the identified candidate')
    names = {'candidate.json', 'publication.json', 'START-HERE.md', 'workstation-' + version + '-windows.zip'}
    checksums = {}
    for line in (args.assets / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if name not in names or name in checksums or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Unexpected release checksum entry')
        checksums[name] = digest
    if set(checksums) != names:
        raise ValueError('The consumer release is incomplete')
    checksums['SHA256SUMS'] = candidate_transport.sha256_file(args.assets / 'SHA256SUMS')
    for name, digest in checksums.items():
        path = args.assets / name
        if path.is_symlink() or candidate_transport.sha256_file(path) != digest:
            raise ValueError('Release asset checksum mismatch: ' + name)
    tag = 'v' + version
    view_command = ['gh', 'release', 'view', tag, '--repo', REPOSITORY, '--json', 'isDraft,assets,targetCommitish,tagName']
    existing = subprocess.run(view_command, capture_output=True, text=True)
    if existing.returncode:
        subprocess.run(['gh', 'release', 'create', tag, '--repo', REPOSITORY, '--target', revision,
                        '--draft', '--title', 'Workstation ' + version,
                        '--notes-file', str(args.assets / 'START-HERE.md')], check=True)
        existing = subprocess.run(view_command, check=True, capture_output=True, text=True)
    metadata = json.loads(existing.stdout)
    if metadata['tagName'] != tag or metadata['targetCommitish'] != revision:
        raise ValueError('The existing release identifies different source code; preserve it')
    uploaded = {asset['name'] for asset in metadata['assets']}
    if uploaded - checksums.keys():
        raise ValueError('The existing release has unexpected assets; inspect it without overwriting them')
    for name, digest in sorted(checksums.items()):
        if name not in uploaded:
            if not metadata['isDraft']:
                raise ValueError('The published release is incomplete; inspect it before modifying public assets')
            subprocess.run(['gh', 'release', 'upload', tag, str(args.assets / name), '--repo', REPOSITORY], check=True)
        with tempfile.TemporaryDirectory(prefix='release-asset-') as temporary:
            subprocess.run(['gh', 'release', 'download', tag, '--repo', REPOSITORY,
                            '--pattern', name, '--dir', temporary], check=True)
            if candidate_transport.sha256_file(Path(temporary) / name) != digest:
                raise ValueError('The remote release asset differs; do not overwrite it: ' + name)
    if metadata['isDraft']:
        subprocess.run(['gh', 'release', 'edit', tag, '--repo', REPOSITORY, '--draft=false'], check=True)
    reference = github_api('git/ref/tags/' + tag)['object']
    if reference['type'] != 'commit' or reference['sha'] != revision:
        raise ValueError('The published release tag does not identify the tested source revision')
    return {'state': 'released', 'version': version,
            'url': 'https://github.com/' + REPOSITORY + '/releases/tag/' + tag}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    publisher = commands.add_parser('publish')
    publisher.add_argument('--directory', type=Path, required=True)
    publisher.add_argument('--report', type=Path, required=True)
    publisher.add_argument('--registry', default='docker.io')
    fetcher = commands.add_parser('fetch')
    fetcher.add_argument('--run-id', type=int, required=True)
    fetcher.add_argument('--directory', type=Path, required=True)
    bundler = commands.add_parser('bundle')
    bundler.add_argument('--directory', type=Path, required=True)
    bundler.add_argument('--report', type=Path, required=True)
    bundler.add_argument('--output', type=Path, required=True)
    releaser = commands.add_parser('release')
    releaser.add_argument('--assets', type=Path, required=True)
    args = parser.parse_args()
    if args.command != 'publish':
        try:
            print(json.dumps({'fetch': fetch, 'bundle': bundle, 'release': release}[args.command](args), indent=2))
            return 0
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            print(str(error), file=sys.stderr)
            return 1
    report = publish(args)
    print(json.dumps(report, indent=2))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())
