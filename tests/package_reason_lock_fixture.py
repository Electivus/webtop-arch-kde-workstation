"""Inject a real stale pacman lock after the owned test transaction releases it."""
import os
from pathlib import Path
import signal
import time


controller = os.getppid()
while controller > 1:
    arguments = Path(f'/proc/{controller}/cmdline').read_bytes().split(b'\0')
    if b'restore' in arguments and any(arg.endswith(b'/workstation-packages') for arg in arguments):
        break
    record = Path(f'/proc/{controller}/status').read_text().splitlines()
    controller = int(next(line.split()[1] for line in record if line.startswith('PPid:')))
else:
    raise RuntimeError('fixture requires an ancestor package restoration command')

os.kill(controller, signal.SIGSTOP)
if os.fork():
    raise SystemExit(0)

# Release all hook pipes so pacman can finish. The owned controller is paused
# until this bounded child has installed the fault; it cannot race ahead to -D.
os.closerange(0, 1024)
try:
    lock = Path('/var/lib/pacman/db.lck')
    deadline = time.monotonic() + 20
    while lock.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError('transaction did not release its lock')
        time.sleep(0.02)
    with lock.open('x') as output:
        output.write('electivus owned package acceptance fault\n')
    Path('/tmp/package-reason-lock-injected').touch()
finally:
    os.kill(controller, signal.SIGCONT)
    os._exit(0)
