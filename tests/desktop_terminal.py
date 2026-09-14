"""Focus an actual Konsole window before typing through the streamed desktop."""
import json
import subprocess
import time


terminal = subprocess.Popen(
    ["konsole", "--separate", "--workdir", "/config"],
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    start_new_session=True)
for _ in range(80):
    found = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(terminal.pid)],
                           capture_output=True, text=True)
    if found.returncode == 0 and found.stdout.strip():
        window = found.stdout.splitlines()[0]
        subprocess.run(["xdotool", "windowactivate", "--sync", window], check=True)
        print(json.dumps({"terminalPid": terminal.pid, "window": window}))
        break
    time.sleep(0.25)
else:
    terminal.terminate()
    terminal.wait(timeout=10)
    raise RuntimeError("The desktop terminal did not open")
