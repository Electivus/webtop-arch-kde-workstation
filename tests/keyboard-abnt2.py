"""Run as abc in a disposable workstation; exercise X11 ABNT2 physical keys."""
import ctypes
import ctypes.util
import json
from pathlib import Path
import subprocess
import time

x11 = ctypes.CDLL(ctypes.util.find_library("X11"))
xtst = ctypes.CDLL(ctypes.util.find_library("Xtst"))
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
display = x11.XOpenDisplay(None)
if not display:
    raise RuntimeError("No X11 display")


def press(keycode, *modifiers):
    for modifier in modifiers:
        xtst.XTestFakeKeyEvent(display, modifier, 1, 0)
    xtst.XTestFakeKeyEvent(display, keycode, 1, 0)
    xtst.XTestFakeKeyEvent(display, keycode, 0, 0)
    for modifier in reversed(modifiers):
        xtst.XTestFakeKeyEvent(display, modifier, 0, 0)
    x11.XSync(display, 0)
    time.sleep(0.08)


terminal = subprocess.Popen(["konsole", "--separate", "-p", "tabtitle=ABNT2 acceptance", "--workdir", "/config"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        found = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(terminal.pid)], capture_output=True, text=True)
        if found.returncode == 0 and found.stdout.strip():
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("The acceptance terminal did not open")
    subprocess.run(["xdotool", "windowactivate", "--sync", found.stdout.splitlines()[0]], check=True)
    time.sleep(0.3)
    result_file = Path("/config/t01-abnt2.txt")
    result_file.unlink(missing_ok=True)
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "20", "printf '%s\\n' '"], check=True)

    # Fixed evdev physical keycodes. Dead acute/tilde/circumflex/diaeresis
    # precede the letter; no composed Unicode character is supplied to X11.
    sequences = [
        [(34,), (38,)],       # acute, A -> a with acute
        [(48,), (38,)],       # tilde, A -> a with tilde
        [(47,)],             # ABNT2 cedilla key
        [(48, 50), (26,)],    # Shift+tilde (circumflex), E
        [(15, 50), (30,)],    # Shift+6 (diaeresis), U
        [(11, 50)],          # Shift+2 -> @
        [(97,)],             # ABNT2 extra slash key
        [(97, 50)],          # Shift+slash -> ?
        [(94, 50)],          # Shift+backslash -> |
    ]
    for index, sequence in enumerate(sequences):
        if index:
            press(65)
        for keys in sequence:
            press(*keys)
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "20", "' > /config/t01-abnt2.txt"], check=True)
    press(36)
    for _ in range(30):
        if result_file.exists():
            break
        time.sleep(0.1)
    received = result_file.read_text(encoding="utf-8").strip()
    if received != "á ã ç ê ü @ / ? |":
        raise AssertionError(f"ABNT2 physical-key composition failed: {received!r}")
    print(json.dumps({"test": "abnt2-physical-key-sequences", "result": "passed", "received": received}, ensure_ascii=False))
finally:
    terminal.terminate()
    terminal.wait(timeout=10)
    x11.XCloseDisplay(display)
