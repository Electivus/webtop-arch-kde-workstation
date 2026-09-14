"""Behavior checks through the shipped command; Docker fixtures are disposable."""
import json
import os
from pathlib import Path
import subprocess
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
CLI = ROOT / ".local" / "cli" / ("workstation.cmd" if WINDOWS else "workstation")
IMAGE = os.environ.get("WORKSTATION_TEST_IMAGE", "electivus/webtop-arch-kde-base:t01")


def invoke(program, *args, **kwargs):
    invocation = [str(program), *map(str, args)]
    if WINDOWS:
        # /s removes only the outer pair; quoted executable and profile paths survive.
        invocation = '"{}" /d /s /c "{}"'.format(
            os.environ.get("COMSPEC", "cmd.exe"), subprocess.list2cmdline(invocation))
    return subprocess.run(invocation, text=True, encoding="utf-8", capture_output=True, timeout=300, **kwargs)


def command(*args, cli=CLI):
    if WINDOWS and args[0] in {"trust", "untrust"}:
        from windows_certificate_dialog import with_certificate_dialog
        profile = args[args.index("--profile") + 1]
        certificate = command("certificate", "--profile", profile, cli=cli)
        result = with_certificate_dialog(certificate["thumbprint"], lambda: invoke(cli, *args))
    else:
        result = invoke(cli, *args)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def docker(*args):
    return subprocess.run(["docker", *args], text=True, encoding="utf-8", capture_output=True, check=True).stdout.strip()


class CommandAcceptance(unittest.TestCase):
    def test_install_start_stop_from_cmd(self):
        name = "ew-test-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / (name + " with spaces")
        try:
            installed = command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                                "--port", "13404", "--memory", "2560", "--cpus", "2", "--no-shortcut")
            self.assertEqual(installed["state"], "installed")
            copied_cli = profile / "tools" / CLI.name
            started = command("start", "--profile", profile, cli=copied_cli)
            self.assertTrue(started["healthy"])
            container = json.loads(docker("inspect", name))[0]
            self.assertEqual(container["NetworkSettings"]["Ports"]["3001/tcp"],
                             [{"HostIp": "127.0.0.1", "HostPort": "13404"}])
            self.assertEqual(container["HostConfig"]["RestartPolicy"]["Name"], "no")
            self.assertEqual(docker("exec", name, "curl", "--fail", "--silent", "--output", "/dev/null",
                                    "--write-out", "%{http_code}", "--cacert", "/config/ssl/cert.pem",
                                    "https://localhost:3001/"), "200")
            import urllib.error
            import urllib.request
            with self.assertRaises(urllib.error.HTTPError) as http:
                urllib.request.urlopen("http://127.0.0.1:13404/")
            self.assertEqual(http.exception.code, 400)
            http.exception.close()
            locale = docker("exec", "--user", "abc", name, "locale")
            self.assertIn("LANG=en_US.UTF-8", locale)
            self.assertIn("LC_TIME=pt_BR.UTF-8", locale)
            self.assertEqual(docker("exec", name, "date", "+%Z,%z"), "-03,-0300")
            self.assertEqual(command("start", "--profile", profile)["containerId"], started["containerId"])
            stopped = command("stop", "--profile", profile)
            self.assertEqual(stopped["state"], "stopped")
            self.assertFalse(stopped["healthy"])
            restarted = command("start", "--profile", profile)
            self.assertEqual(restarted["containerId"], started["containerId"])
            self.assertTrue(restarted["healthy"])
            certificate = command("certificate", "--profile", profile)
            self.assertEqual(certificate["dnsName"], "localhost")
            self.assertEqual(len(certificate["sha256"]), 64)
            docker("cp", str(ROOT / "tests" / "keyboard-abnt2.py"), name + ":/config/keyboard-abnt2.py")
            keyboard = json.loads(docker("exec", "--user", "abc", name, "python3", "/config/keyboard-abnt2.py"))
            self.assertEqual(keyboard["received"], "á ã ç ê ü @ / ? |")
            (profile / "lifecycle-result.json").write_text(json.dumps(
                {"test": "lifecycle-via-cmd", "result": "passed", "status": restarted, "keyboard": keyboard},
                indent=2), encoding="utf-8")
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)

    def test_foreign_resources_are_preserved(self):
        name = "ew-isolation-" + uuid.uuid4().hex[:10]
        directory = ROOT / ".local" / name
        container_id = docker("create", "--name", name, "--entrypoint", "/bin/true", IMAGE)
        volume = name + "-volume-home"
        try:
            refused = invoke(CLI, "install", "--profile", directory / "container", "--name", name,
                             "--image", IMAGE, "--memory", "2048", "--cpus", "2", "--no-shortcut")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("belongs to another installation", refused.stderr)
            self.assertEqual(docker("inspect", "--format", "{{.Id}}", name), container_id)
            docker("volume", "create", volume)
            before = docker("volume", "inspect", volume)
            command("install", "--profile", directory / "volume", "--name", name + "-volume",
                    "--image", IMAGE, "--memory", "2048", "--cpus", "2", "--no-shortcut")
            refused = invoke(CLI, "start", "--profile", directory / "volume")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("volume belongs to another installation", refused.stderr)
            self.assertEqual(docker("volume", "inspect", volume), before)
        finally:
            docker("container", "rm", "-v", container_id)
            subprocess.run(["docker", "volume", "rm", volume], capture_output=True)

    @unittest.skipUnless(WINDOWS, "Windows native shell and certificate APIs")
    def test_windows_bundle_shortcut_and_trust(self):
        import ssl
        import urllib.request

        name = "ew-test-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / (name + " native shortcut")
        bundle = ROOT / ".local" / (name + " extracted commands")
        setup = invoke(ROOT / "distribution" / "windows" / "setup.cmd", IMAGE, bundle)
        self.assertEqual(setup.returncode, 0, setup.stderr + setup.stdout)
        extracted_cli = bundle / "workstation.cmd"
        certificate = None
        try:
            installed = command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                                "--port", "13405", "--memory", "2560", "--cpus", "2", cli=extracted_cli)
            self.assertTrue(Path(installed["shortcut"]).is_file())
            # Execute the delivered .lnk through the Windows Shell.
            os.startfile(installed["shortcut"])
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                state = command("status", "--profile", profile)
                if state["healthy"]:
                    break
                time.sleep(2)
            self.assertTrue(state["healthy"], state)
            certificate = command("certificate", "--profile", profile)
            command("trust", "--profile", profile)
            # A fresh default TLS context loads the current-user Windows trust store.
            with urllib.request.urlopen(state["url"], context=ssl.create_default_context()) as response:
                self.assertEqual(response.status, 200)
            command("untrust", "--profile", profile)
            command("untrust", "--profile", profile)  # removing an absent leaf is idempotent
            fingerprint = bytes.fromhex(certificate["thumbprint"])
            import hashlib
            self.assertFalse(any(hashlib.sha1(der).digest() == fingerprint
                                 for der, encoding, trust in ssl.enum_certificates("ROOT")))
        finally:
            if certificate:
                command("untrust", "--profile", profile)
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
