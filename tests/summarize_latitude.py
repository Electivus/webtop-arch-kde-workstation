"""Summarize completed Latitude phases for one identified CI candidate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


def summary(values):
    ordered = sorted(values)
    if not ordered:
        return {'samples': 0}
    return {'samples': len(ordered), 'min': round(ordered[0], 3),
            'median': round(statistics.median(ordered), 3),
            'p95': round(ordered[math.ceil(len(ordered) * .95) - 1], 3),
            'max': round(ordered[-1], 3)}


def memory_gib(value):
    match = re.fullmatch(r'([0-9.]+)(B|[KMGT]i?B)', value.split(' / ')[0])
    if not match:
        raise ValueError('Unknown Docker memory unit: ' + value)
    amount, unit = match.groups()
    exponent = 0 if unit == 'B' else 'KMGT'.index(unit[0]) + 1
    return float(amount) * (1024 if 'i' in unit else 1000) ** exponent / 1024 ** 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    candidate = json.loads(args.manifest.read_text())
    image = next(item for item in candidate['images'] if item['variant'] == 'salesforce')
    profile = json.loads((args.directory / 'profile/profile.json').read_text())
    report = {'candidate': {'version': candidate['version'], 'revision': candidate['revision'],
                            'digest': image['digest']}, 'containerLimits': {
                                'memoryMiB': profile['memoryMiB'], 'cpus': profile['cpus']},
              'phases': {}, 'sources': {}, 'statistics': 'p95 uses nearest rank; Docker CPU sums logical processors.'}
    measurement_files = None
    for phase in ('prepare', 'measure', 'gui'):
        result_path = args.directory / (phase + '.json')
        resource_path = args.directory / (phase + '-resources.jsonl')
        result = json.loads(result_path.read_text())
        if result.get('state') != 'passed' or result['image'] != image['digest']:
            raise ValueError(phase + ': require a passed phase against the selected candidate digest')
        if any(step['state'] != 'passed' for step in result['steps']):
            raise ValueError(phase + ': not all recorded steps passed')
        if measurement_files is None:
            measurement_files = result['measurementFilesSha256']
        elif result['measurementFilesSha256'] != measurement_files:
            raise ValueError(phase + ': measurement tools changed between the retained phases')
        for path in (result_path, resource_path):
            report['sources'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        samples = [json.loads(line) for line in resource_path.read_text().splitlines()]
        groups = {}
        for step in result['steps']:
            selected = [sample for sample in samples if sample['phase'] == step['name']]
            workstation = [container for sample in selected for container in sample.get('containers', [])
                           if container['Name'] == profile['name']]
            others = [[container for container in sample['containers'] if container['Name'] != profile['name']]
                      for sample in selected if 'containers' in sample]
            groups[step['name']] = {
                'durationSeconds': step['durationSeconds'], 'resourceSamples': len(selected),
                'collectionErrors': sum('collectionError' in sample for sample in selected),
                'windowsCpuPercent': summary(sample['windowsCpuPercent'] for sample in selected
                                             if sample.get('windowsCpuPercent') is not None),
                'windowsAvailableGiB': summary(sample['windowsMemory']['availableBytes'] / 1024 ** 3
                                               for sample in selected if 'windowsMemory' in sample),
                'workstationCpuPercent': summary(float(row['CPUPerc'].rstrip('%')) for row in workstation),
                'workstationMemoryGiB': summary(memory_gib(row['MemUsage']) for row in workstation),
                'otherContainersCpuPercent': summary(sum(float(row['CPUPerc'].rstrip('%')) for row in rows)
                                                     for rows in others),
                'otherContainersMemoryGiB': summary(sum(memory_gib(row['MemUsage']) for row in rows)
                                                    for rows in others)}
        report['phases'][phase] = groups
        if phase == 'gui':
            steady = groups['steady-desktop']
            for metric in ('windowsCpuPercent', 'windowsAvailableGiB',
                           'workstationCpuPercent', 'workstationMemoryGiB'):
                if steady[metric]['samples'] < 10:
                    raise ValueError('The steady desktop has fewer than ten valid resource samples: ' + metric)
            report.update(hardware=result['hardware'], engine=result['engine'],
                          controllerSha256=result['controllerSha256'],
                          measurementScriptSha256=result['scriptSha256'],
                          measurementFilesSha256=measurement_files)
            response = next(step['result'] for step in result['steps'] if step['name'] == 'visible-response')
            match = re.search(r'^### Result\r?\n([^\r\n]+)', response, re.MULTILINE)
            if not match:
                raise ValueError('The browser returned no structured response measurements')
            measured = json.loads(match[1])
            report['visibleResponse'] = {'milliseconds': summary(item['milliseconds'] for item in measured['samples']),
                                         'method': measured['method'], 'canvas': measured['canvas']}
            report['rendering'] = next(step['result'] for step in result['steps'] if step['name'] == 'rendering')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
