"""Run on Windows; developer-only measurement, never a destination prerequisite.

Preparation and measurement are separate so a failed visual probe can be resumed
without representing an existing profile as a fresh installation.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import time

from test_commands import command, docker, invoke, ROOT, CLI
from windows_resources import hardware, ResourceRecorder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'measure', 'gui', 'stop'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--network-config', type=Path)
    parser.add_argument('--memory', type=int, default=6144)
    parser.add_argument('--cpus', type=int, default=4)
    args = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('Use native Windows Python for this developer measurement.')
    directory = args.directory.resolve()
    profile = directory / 'profile'
    if args.phase == 'stop':
        print(json.dumps(command('stop', '--profile', profile), indent=2))
        return
    if args.phase == 'prepare':
        directory.mkdir(parents=True, exist_ok=False)
    elif not (directory / 'prepare.json').is_file():
        raise SystemExit('Complete and retain the initial preparation measurement first.')
    if args.phase != 'prepare':
        if json.loads((directory / 'prepare.json').read_text()).get('state') != 'passed':
            raise SystemExit('The initial preparation did not pass; diagnose it before recording warm starts.')
        installed = json.loads((profile / 'profile.json').read_text())
        if (installed['name'], installed['image'], installed['memoryMiB'], installed['cpus']) != (
                args.name, args.image, args.memory, args.cpus):
            raise SystemExit('The selected measurement must match the retained installation and resource limits.')
    report = {'phase': args.phase, 'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'image': json.loads(docker('image', 'inspect', args.image))[0]['Id'],
              'hardware': hardware(), 'engine': json.loads(docker('info', '--format', '{{json .}}')),
              'controllerSha256': hashlib.sha256(CLI.with_name('workstation.exe').read_bytes()).hexdigest(),
              'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'steps': []}
    # Retain only nonpersonal engine properties needed to identify the platform.
    report['engine'] = {key: report['engine'][key] for key in (
        'ID', 'ServerVersion', 'OperatingSystem', 'OSType', 'Architecture', 'KernelVersion', 'NCPU', 'MemTotal')}
    result_path = directory / (args.phase + '.json')
    if result_path.exists():
        raise SystemExit('Archive the existing phase reports as a separate attempt before repeating; evidence is not overwritten.')
    recorder = ResourceRecorder(directory / (args.phase + '-resources.jsonl'))
    recorder.start()

    def save():
        result_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    def step(name, operation):
        recorder.phase = name
        started = time.monotonic()
        row = {'name': name, 'state': 'running'}
        report['steps'].append(row)
        save()
        print('START ' + name, flush=True)
        try:
            row['result'] = operation()
            row['state'] = 'passed'
            return row['result']
        except Exception as error:
            row.update(state='failed', error=str(error))
            raise
        finally:
            row['durationSeconds'] = round(time.monotonic() - started, 3)
            save()
            print(row['state'].upper() + ' ' + name, flush=True)

    try:
        step('baseline', lambda: time.sleep(20))
        if args.phase == 'prepare':
            exchange = directory / 'exchange'
            exchange.mkdir()
            options = ['install', '--profile', profile, '--name', args.name, '--image', args.image,
                       '--port', '14512', '--memory', str(args.memory), '--cpus', str(args.cpus),
                       '--exchange', exchange]
            if args.network_config:
                options += ['--network-config', args.network_config]
            step('install', lambda: command(*options))
            step('first-start', lambda: command('start', '--profile', profile))
            step('first-preparation', lambda: command('prepare', '--profile', profile))
            step('network', lambda: command('network', '--profile', profile, '--check'))
            step('stop', lambda: command('stop', '--profile', profile))
        elif args.phase == 'measure':
            for attempt in range(3):
                step('warm-start-' + str(attempt + 1), lambda: command('start', '--profile', profile))
                step('warm-preparation-' + str(attempt + 1), lambda: command('prepare', '--profile', profile))
                step('warm-stop-' + str(attempt + 1), lambda: command('stop', '--profile', profile))
            # GUI scenario is performed from the retained profile after warm starts.
            step('desktop-start', lambda: command('start', '--profile', profile))
        else:
            browser = shutil.which('playwright-cli.cmd')
            if not browser:
                raise RuntimeError('This developer visual measurement needs playwright-cli and Chrome on Windows.')
            environment = dict(os.environ)
            environment.pop('PLAYWRIGHT_MCP_CDP_ENDPOINT', None)
            session = 'latitude-' + args.name

            def playwright(*arguments):
                result = invoke(browser, '-s=' + session, *arguments, cwd=ROOT, env=environment, timeout=180)
                with (directory / 'browser.log').open('a', encoding='utf-8') as log:
                    log.write(result.stdout + result.stderr)
                if result.returncode or '### Error' in result.stdout:
                    raise RuntimeError(result.stdout + result.stderr)
                return result.stdout

            def window(pattern):
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    result = subprocess.run(['docker', 'exec', '--user', 'abc', args.name, 'xdotool',
                                             'search', '--onlyvisible', '--name', pattern],
                                            capture_output=True, text=True, timeout=15)
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.splitlines()[0]
                    time.sleep(0.5)
                raise RuntimeError('Desktop window not ready: ' + pattern)

            state = command('start', '--profile', profile)
            certificate = command('certificate', '--profile', profile)
            trusted_before = any(hashlib.sha1(der).hexdigest().upper() == certificate['thumbprint']
                                 for der, encoding, trust in ssl.enum_certificates('ROOT'))
            try:
                step('trust', lambda: command('trust', '--profile', profile))
                step('browser-connect', lambda: playwright('open', state['url'], '--browser=chrome', '--headed'))
                step('viewport', lambda: playwright('resize', '1920', '1080'))

                def open_apps():
                    project = '/config/projects/latitude-demo'
                    exists = subprocess.run(['docker', 'exec', args.name, 'test', '-f', project + '/sfdx-project.json'],
                                            capture_output=True).returncode == 0
                    if not exists:
                        generated = json.loads(docker('exec', '--user', 'abc', args.name, 'sf', 'project', 'generate',
                                                      '--name', 'latitude-demo', '--output-dir', '/config/projects', '--json'))
                        if generated.get('status') != 0:
                            raise RuntimeError('Salesforce project generation failed')
                    docker('cp', str(ROOT / 'tests/salesforce_sample') + '/.', args.name + ':' + project)
                    docker('cp', str(ROOT / 'tests/latitude-probe.html'), args.name + ':/config/latitude-probe.html')
                    docker('exec', args.name, 'chown', '-R', '1000:1000', project)
                    docker('exec', '--user', 'abc', args.name, 'python3', '-c',
                           'from pathlib import Path; import sys; p=Path(sys.argv[1]); '
                           'p.write_text(p.read_text().replace("return 1\\n", "return 1;\\n"))',
                           project + '/force-app/main/default/classes/WorkstationProbe.cls')
                    docker('exec', '--detach', '--user', 'abc', args.name, 'code-insiders', '--new-window',
                           '--disable-workspace-trust', '--skip-welcome', '--skip-release-notes', project)
                    editor_window = window('Visual Studio Code - Insiders')
                    for relative in ('force-app/main/default/lwc/workstationProbe/workstationProbe.html',
                                     'force-app/main/default/classes/WorkstationProbe.cls'):
                        docker('exec', '--user', 'abc', args.name, 'code-insiders', '--reuse-window',
                               '--goto', project + '/' + relative + ':1')
                    docker('exec', '--user', 'abc', args.name, 'xdotool', 'windowsize', editor_window, '930', '940',
                           'windowmove', editor_window, '10', '45')
                    docker('exec', '--detach', '--user', 'abc', args.name, 'google-chrome', '--no-first-run',
                           '--no-default-browser-check', '--new-window', 'file:///config/latitude-probe.html')
                    chrome_window = window('^Electivus Full HD probe')
                    docker('exec', '--user', 'abc', args.name, 'xdotool', 'windowsize', chrome_window, '940', '940',
                           'windowmove', chrome_window, '960', '45', 'windowactivate', '--sync', chrome_window)
                    return {'project': project, 'editorWindow': editor_window, 'chromeWindow': chrome_window,
                            'xrandr': docker('exec', '--user', 'abc', args.name, 'xrandr', '--current')}

                step('open-applications', open_apps)
                docker('cp', str(ROOT / 'tests/rendering_probe.py'), args.name + ':/config/rendering_probe.py')
                step('rendering', lambda: json.loads(docker('exec', '--user', 'abc', args.name,
                                                          'python3', '/config/rendering_probe.py')))
                step('steady-desktop', lambda: time.sleep(120))
                processes = docker('exec', '--user', 'abc', args.name, 'ps', '-u', 'abc', '-o', 'comm=')
                report['applicationProcessNames'] = sorted(set(processes.splitlines()))
                if 'java' not in report['applicationProcessNames']:
                    raise RuntimeError('The Salesforce Java service did not start after opening the Apex file')
                step('visible-response', lambda: playwright('run-code', '--filename=tests/Latitude-Response.js'))
                shutil.copyfile(ROOT / '.local/latitude-desktop.png', directory / 'desktop.png')
            finally:
                try:
                    playwright('close')
                finally:
                    if not trusted_before:
                        command('untrust', '--profile', profile)
            step('stop', lambda: command('stop', '--profile', profile))
        report['state'] = 'passed'
    except Exception as error:
        report.update(state='failed', error=str(error))
        raise
    finally:
        recorder.stop()
        report['completedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()


if __name__ == '__main__':
    main()
