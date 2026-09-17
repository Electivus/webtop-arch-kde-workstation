"""Exercise the supplied Code Analyzer CLI on disposable Apex, without an org."""
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    inspected = subprocess.run(['sf', 'plugins', 'inspect', '@salesforce/plugin-code-analyzer', '--json'],
                               capture_output=True, text=True, check=True)
    plugins = json.loads(inspected.stdout)
    plugin = next(entry for entry in plugins if entry['name'] == '@salesforce/plugin-code-analyzer')
    if plugin['type'] == 'jit':
        raise RuntimeError('Code Analyzer must be installed before its first use')
    with tempfile.TemporaryDirectory(prefix='analyzer-probe-', dir=Path.home() / 'projects') as directory:
        root = Path(directory)
        (root / 'AnalyzerProbe.cls').write_text(
            'public class AnalyzerProbe { public static void test() { '
            'try { Integer value = 1; } catch (Exception e) {} } }\n')
        subprocess.run(['sf', 'code-analyzer', 'run', '--workspace', str(root),
                        '--rule-selector', 'pmd:EmptyCatchBlock', '--output-file', str(root / 'result.json')],
                       capture_output=True, text=True, check=True, timeout=180)
        result = json.loads((root / 'result.json').read_text())
        violations = result['violations']
        if not any(entry['rule'] == 'EmptyCatchBlock' and entry['engine'] == 'pmd' for entry in violations):
            raise RuntimeError('Code Analyzer did not find the intentional empty Apex catch block')
        print(json.dumps({'plugin': plugin['name'], 'version': plugin['version'],
                          'rule': 'pmd:EmptyCatchBlock', 'violations': len(violations)}))


if __name__ == '__main__':
    main()
