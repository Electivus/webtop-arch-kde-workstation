"""Read the active KDE compositor on the disposable desktop being measured."""
import json
import os
from pathlib import Path
import subprocess


environment = dict(os.environ)
for process in Path('/proc').iterdir():
    if not process.name.isdigit():
        continue
    try:
        if (process / 'comm').read_text().strip() not in ('plasmashell', 'kwin_x11'):
            continue
        for entry in (process / 'environ').read_bytes().split(b'\0'):
            if entry.startswith(b'DBUS_SESSION_BUS_ADDRESS='):
                environment['DBUS_SESSION_BUS_ADDRESS'] = entry.split(b'=', 1)[1].decode()
        if 'DBUS_SESSION_BUS_ADDRESS' in environment:
            break
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
result = subprocess.run(['qdbus6', 'org.kde.KWin', '/KWin', 'supportInformation'],
                        env=environment, capture_output=True, text=True, timeout=20)
report = {'directRenderingDevices': [p.name for p in Path('/dev/dri').glob('*')],
          'kwin': {'exitCode': result.returncode,
                   'lines': [line for line in result.stdout.splitlines() if any(
                       key in line.lower() for key in ('composit', 'opengl', 'renderer', 'driver', 'llvmpipe', 'platform'))]}}
if result.returncode:
    report['kwin']['error'] = result.stderr.strip()
print(json.dumps(report, indent=2))
raise SystemExit(result.returncode)
