"""Executed by Python inside the workstation, never by Python on Windows."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def run(*args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, timeout=600, **kwargs)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed: {result.stderr.strip() or result.stdout.strip()}')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'mutate', 'restored'))
    parser.add_argument('--engine')
    parser.add_argument('--project-name')
    parser.add_argument('--variant', choices=('base', 'salesforce'))
    args = parser.parse_args()
    marker = Path('/config/projects/destination-verification.txt')
    if args.action == 'mutate':
        marker.write_text('changed after backup\n')
        return
    if args.action == 'restored':
        if marker.read_text() != 'saved before backup\n':
            raise RuntimeError('Recovery did not restore the saved project marker')
        print(json.dumps({'restoredProject': True}))
        return
    if not args.engine or not args.project_name or not args.variant:
        raise ValueError('Check requires the expected engine, Compose project name and image variant')
    report = {'state': 'running', 'checks': {}}
    checks = report['checks']
    try:
        connection = json.loads(run('workstation-docker-check'))
        if connection['engineId'] != args.engine:
            raise RuntimeError('The desktop does not reach the notebook Docker engine')
        checks['docker'] = connection
        checks['git'] = run('git', '--version')
        checks['zsh'] = run('zsh', '--version')
        checks['chrome'] = run('google-chrome', '--version')
        html = run('google-chrome', '--headless', '--dump-dom',
                   'data:text/html,<title>Destination verification</title><h1>browser-ready</h1>')
        if '<h1>browser-ready</h1>' not in html:
            raise RuntimeError('Chrome did not render the verification page')
        checks['chromeRendered'] = True
        checks['locale'] = run('locale')
        checks['keyboard'] = run('setxkbmap', '-query')
        checks['display'] = run('xrandr', '--current')
        if args.variant == 'salesforce':
            checks['salesforce'] = run('sf', '--version')
            plugins = json.loads(run('sf', 'plugins', 'inspect', '@salesforce/plugin-code-analyzer', '--json'))
            checks['codeAnalyzer'] = next({'name': item['name'], 'version': item['version']}
                                         for item in plugins if item['name'] == '@salesforce/plugin-code-analyzer'
                                         and item.get('type') != 'jit')
            checks['java'] = run('java', '--version')
            checks['node'] = run('node', '--version')
            for editor in ('code', 'code-insiders'):
                checks[editor] = {'version': run(editor, '--version'),
                                  'extensions': run(editor, '--list-extensions', '--show-versions').splitlines()}
                if not any(extension.startswith('salesforce.salesforcedx-vscode@')
                           for extension in checks[editor]['extensions']):
                    raise RuntimeError(editor + ' has no Salesforce Extension Pack')
            generated = json.loads(run('sf', 'project', 'generate', '--name', 'destination-salesforce',
                                       '--output-dir', '/config/projects', '--json'))
            if generated.get('status') != 0:
                raise RuntimeError('Salesforce project generation failed')
            checks['salesforceProject'] = True
        exchange = Path('/exchange')
        if (exchange / 'from-windows.txt').read_text().strip() != 'windows-to-linux':
            raise RuntimeError('The Windows exchange file could not be read')
        (exchange / 'from-linux.txt').write_text('linux-to-windows\n')
        checks['exchange'] = True
        marker.write_text('saved before backup\n')
        project = Path('/config/projects/destination-compose')
        shutil.copytree('/etc/electivus/examples/compose-demo', project)
        (project / 'input.txt').write_text('destination-project\n')
        environment = dict(os.environ, COMPOSE_PROJECT_NAME=args.project_name,
                           WORKSTATION_PROJECT_SUBPATH=project.name)
        try:
            run('docker', 'compose', 'up', '--detach', '--build', '--wait', '--wait-timeout', '60',
                cwd=project, env=environment)
            if (project / 'result.txt').read_text().strip() != 'worker: destination-project':
                raise RuntimeError('Compose did not write to the Linux project')
            checks['composeBuildAndWrite'] = True
        finally:
            run('docker', 'compose', 'down', '--rmi', 'all', cwd=project, env=environment)
        report['state'] = 'passed'
    except Exception as error:
        report.update(state='failed', error=str(error))
        raise
    finally:
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
