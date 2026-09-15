#!/usr/bin/env python3
"""Execute the repository's acceptance contract and retain each check's result."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_report(output, report):
    temporary = output / 'acceptance.json.tmp'
    temporary.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output / 'acceptance.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, default=ROOT / 'tests/acceptance.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.contract.read_bytes()
    contract = json.loads(raw)
    if contract.get('schemaVersion') != 1 or not contract.get('checks'):
        raise ValueError('The acceptance contract must have schemaVersion 1 and at least one check.')
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'schemaVersion': 1, 'state': 'running', 'startedAt': timestamp(),
              'contractSha256': hashlib.sha256(raw).hexdigest(),
              'checks': [dict(check, state='not-run') for check in contract['checks']]}
    write_report(args.output, report)
    for check in report['checks']:
        started = time.monotonic()
        check.update(state='running', startedAt=timestamp())
        write_report(args.output, report)
        print('START ' + check['id'], flush=True)
        try:
            if check.get('variant', 'base') not in ('base', 'salesforce'):
                raise ValueError('Unknown acceptance variant: ' + str(check['variant']))
            environment = os.environ.copy()
            if check.get('variant', 'base') == 'salesforce':
                environment['WORKSTATION_TEST_IMAGE'] = environment['WORKSTATION_SALESFORCE_TEST_IMAGE']
            with (args.output / (check['id'] + '.log')).open('w', encoding='utf-8') as log:
                process = subprocess.run([sys.executable, str(ROOT / check['script']), *check.get('args', [])],
                                         cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=5400)
            check.update(state='passed' if process.returncode == 0 else 'failed', exitCode=process.returncode)
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            check.update(state='failed', error=str(error))
        check.update(completedAt=timestamp(), durationSeconds=round(time.monotonic() - started, 3))
        print(check['state'].upper() + ' ' + check['id'], flush=True)
        if check['state'] == 'failed':
            report.update(state='failed', completedAt=timestamp())
            if 'error' in check:
                report['error'] = check['error']
            write_report(args.output, report)
            return 1
        write_report(args.output, report)
    report.update(state='passed', completedAt=timestamp())
    write_report(args.output, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
