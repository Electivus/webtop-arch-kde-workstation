"""Developer measurement through native Windows APIs and the Docker CLI."""
import ctypes
from ctypes import wintypes
import datetime
import json
import subprocess
import threading
import time
import winreg


class MemoryStatus(ctypes.Structure):
    _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
        (name, ctypes.c_ulonglong) for name in (
            'totalPhysical', 'availablePhysical', 'totalPageFile', 'availablePageFile',
            'totalVirtual', 'availableVirtual', 'availableExtendedVirtual')]


def memory():
    value = MemoryStatus()
    value.length = ctypes.sizeof(value)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):
        raise ctypes.WinError()
    return {'physicalBytes': value.totalPhysical, 'availableBytes': value.availablePhysical,
            'loadPercent': value.load}


def cpu_times():
    values = [wintypes.FILETIME() for _ in range(3)]
    if not ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(value) for value in values)):
        raise ctypes.WinError()
    return tuple((value.dwHighDateTime << 32) | value.dwLowDateTime for value in values)


def hardware():
    result = memory()
    for key, names in (
        (r'HARDWARE\DESCRIPTION\System\BIOS', ('SystemManufacturer', 'SystemProductName')),
        (r'HARDWARE\DESCRIPTION\System\CentralProcessor\0', ('ProcessorNameString',)),
    ):
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as handle:
            for name in names:
                result[name] = winreg.QueryValueEx(handle, name)[0]
    ctypes.windll.user32.SetProcessDPIAware()
    result['display'] = {'width': ctypes.windll.user32.GetSystemMetrics(0),
                         'height': ctypes.windll.user32.GetSystemMetrics(1),
                         'monitorCount': ctypes.windll.user32.GetSystemMetrics(80)}
    return result


class ResourceRecorder:
    """Keep the samples, including collection failures; never synthesize zero load."""

    def __init__(self, path):
        self.path = path
        self.phase = 'baseline'
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.collect, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=25)
        if self.thread.is_alive():
            raise RuntimeError('Resource collection did not stop')

    def collect(self):
        previous = cpu_times()
        with self.path.open('x', encoding='utf-8') as output:
            while not self.stopped.wait(2):
                sample = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'phase': self.phase, 'monotonic': time.monotonic()}
                try:
                    current = cpu_times()
                    idle, kernel, user = (now - before for now, before in zip(current, previous))
                    total = kernel + user  # Kernel time includes idle time.
                    sample['windowsCpuPercent'] = 100 * (total - idle) / total if total > 0 else None
                    previous = current
                    sample['windowsMemory'] = memory()
                    result = subprocess.run(['docker', 'stats', '--no-stream', '--format', '{{json .}}'],
                                            capture_output=True, text=True, encoding='utf-8', timeout=20)
                    if result.returncode:
                        raise RuntimeError('Docker statistics unavailable: ' + result.stderr.strip())
                    sample['containers'] = [json.loads(line) for line in result.stdout.splitlines() if line]
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                    sample['collectionError'] = str(error)
                output.write(json.dumps(sample) + '\n')
                output.flush()
