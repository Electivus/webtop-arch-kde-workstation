"""Open delivered applications through the streamed desktop on Windows."""
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import time
import uuid

from test_commands import command, docker, invoke, ROOT
from test_preparation import IMAGE


def main():
    name = "ew-gui-" + uuid.uuid4().hex[:10]
    profile = ROOT / ".local" / name
    session = "ew-browser-" + uuid.uuid4().hex[:8]
    browser = shutil.which("playwright-cli.cmd")
    if os.name != "nt" or not browser:
        raise SystemExit("Run on Windows with Chrome and playwright-cli.")
    env = dict(os.environ)
    env.pop("PLAYWRIGHT_MCP_CDP_ENDPOINT", None)
    trusted_before = False
    certificate = None

    def playwright(*args):
        result = invoke(browser, "-s=" + session, *args, env=env, cwd=ROOT)
        with (profile / "browser.log").open("a", encoding="utf-8") as log:
            log.write(result.stdout + result.stderr)
        if result.returncode or "### Error" in result.stdout:
            raise AssertionError(result.stdout + result.stderr)

    def wait_for_desktop(*args):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            result = subprocess.run(["docker", "exec", "--user", "abc", name, *args],
                                    capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return result.stdout.strip()
            time.sleep(0.5)
        raise AssertionError("Desktop did not reach the expected state: " + repr(args))

    try:
        command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                "--port", "13411", "--memory", "2560", "--cpus", "2", "--no-shortcut")
        state = command("start", "--profile", profile)
        prepared = command("prepare", "--profile", profile)
        certificate = command("certificate", "--profile", profile)
        trusted_before = any(hashlib.sha1(der).hexdigest().upper() == certificate["thumbprint"]
                             for der, encoding, trust in ssl.enum_certificates("ROOT"))
        command("trust", "--profile", profile)
        playwright("open", state["url"], "--browser=chrome")
        docker("cp", str(ROOT / "tests/desktop_terminal.py"), name + ":/config/desktop_terminal.py")
        terminal = json.loads(docker("exec", "--user", "abc", name, "python3", "/config/desktop_terminal.py"))
        playwright("run-code", "--filename=tests/Browser-Applications.js")
        wait_for_desktop("test", "-f", "/config/t02-terminal-ready")
        playwright("screenshot", "--filename=.local/t02-terminal.png")
        playwright("run-code", "--filename=tests/Browser-Chrome.js")
        # The real X11 window title changes from Loading only after the page loads.
        chrome_window = wait_for_desktop("xdotool", "search", "--onlyvisible", "--name", "^workstation browser").splitlines()[0]
        chrome_title = docker("exec", "--user", "abc", name, "xdotool", "getwindowname", chrome_window)
        playwright("screenshot", "--filename=.local/t02-chrome.png")
        processes = docker("exec", "--user", "abc", name, "ps", "-u", "abc", "-o", "args=")
        assert "--type=renderer" in processes, processes
        assert "--no-sandbox" not in processes, processes
        result = {"test": "chrome-and-terminal-through-desktop", "result": "passed",
                  "status": state, "preparation": prepared, "terminal": terminal, "chromeTitle": chrome_title,
                  "screenshots": [".local/t02-terminal.png", ".local/t02-chrome.png"]}
        (profile / "browser-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
    finally:
        invoke(browser, "-s=" + session, "close", env=env, cwd=ROOT)
        if certificate and not trusted_before:
            command("untrust", "--profile", profile)
        subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
        subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    main()
