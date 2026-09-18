"""Developer-only browser acceptance; the destination needs CMD and Docker only."""
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import uuid

from test_commands import command, docker, invoke, ROOT, IMAGE
from test_packages import configure_test_network


def main():
    if os.name != "nt":
        raise SystemExit("Run this browser acceptance on Windows with Chrome and playwright-cli.")
    name = "ew-test-" + uuid.uuid4().hex[:10]
    profile = ROOT / ".local" / name
    session = "ew-browser-" + uuid.uuid4().hex[:8]
    browser = shutil.which("playwright-cli.cmd")
    if not browser:
        raise SystemExit("Install playwright-cli for this developer browser test.")
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

    try:
        command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                "--port", "13406", "--memory", "2560", "--cpus", "2", "--no-shortcut")
        configure_test_network(profile)
        state = command("start", "--profile", profile)
        certificate = command("certificate", "--profile", profile)
        trusted_before = any(hashlib.sha1(der).hexdigest().upper() == certificate["thumbprint"]
                             for der, encoding, trust in ssl.enum_certificates("ROOT"))
        command("trust", "--profile", profile)
        playwright("open", state["url"], "--browser=chrome")
        command("prepare", "--profile", profile)
        docker("cp", str(ROOT / "tests/desktop_terminal.py"), name + ":/config/desktop_terminal.py")
        docker("exec", "--user", "abc", name, "python3", "/config/desktop_terminal.py")
        playwright("run-code", "--filename=tests/Browser-Session.js")
        typed = docker("exec", "--user", "abc", name, "cat", "/config/t01-typing.txt")
        assert typed == "ação ç áéíóú ãõ ê ü @ / ? |", typed
        probe = """set -eu
task_pid=$(cat /config/t01-task.pid)
kill -0 "$task_pid"
test "$(ps -p "$task_pid" -o lstart=)" = "$(cat /config/t01-task.start)"
before=$(cat /config/t01-task.tick)
sleep 2
after=$(cat /config/t01-task.tick)
test "$after" -gt "$before"
printf 'pid=%s before=%s after=%s\\n' "$task_pid" "$before" "$after"
"""
        task = docker("exec", "--user", "abc", name, "bash", "-c", probe)
        result = {"test": "desktop-browser-via-cmd", "result": "passed", "typed": typed,
                  "task": task, "status": state,
                  "screenshots": [".local/t01-before-disconnect.png", ".local/t01-after-reconnect.png"]}
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
