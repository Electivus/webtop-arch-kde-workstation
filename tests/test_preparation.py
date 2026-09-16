"""Application preparation through the shipped CMD/Linux command."""
import os
import json
from pathlib import Path
import subprocess
import time
import unittest
import uuid

from test_commands import ROOT, CLI, command, docker, invoke

IMAGE = os.environ.get("WORKSTATION_TEST_IMAGE", "electivus/webtop-arch-kde-base:t02")


class PreparationAcceptance(unittest.TestCase):
    def assert_automatic_preparation_checks_manifest(self, name, profile):
        manifest = "/config/.local/share/electivus/apps/chrome/current/manifest.json"
        original = docker("exec", "--user", "abc", name, "cat", manifest)
        changed = json.loads(original)
        changed["actualVersion"] += " incompatible"
        write = "from pathlib import Path; import sys; Path(sys.argv[1]).write_text(sys.argv[2])"
        try:
            docker("exec", "--user", "abc", name, "python3", "-c", write, manifest, json.dumps(changed))
            command("stop", "--profile", profile)
            command("start", "--profile", profile)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                state = command("prepare", "--profile", profile, "--status")
                if state["state"] == "failed":
                    break
                time.sleep(0.5)
            self.assertEqual(state["state"], "failed", "automatic preparation must check persisted version receipts")
            self.assertIn("Persisted chrome", state["error"])
            (profile / "incompatible-manifest-result.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        finally:
            docker("exec", "--user", "abc", name, "python3", "-c", write, manifest, original)

    def test_failed_install_resumes_from_verified_download(self):
        name = "ew-retry-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13409", "--memory", "2560", "--cpus", "2", "--no-shortcut")
            # Let the public command establish the home and its image identity.
            # Block downloads until the failing installation fixture is ready.
            offline = profile / "offline-input.json"
            offline.write_text(json.dumps({"proxy": "http://127.0.0.1:9"}), encoding="utf-8")
            command("network", "--profile", profile, "--network-config", offline)
            command("start", "--profile", profile)
            destination = "/config/.local/share/electivus/apps/chrome/versions"
            docker("exec", "--user", "abc", name, "sh", "-c",
                   'mkdir -p "$1" && chmod 555 "$1"', "fixture", destination)
            command("stop", "--profile", profile)
            command("network", "--profile", profile, "--clear")
            command("start", "--profile", profile)
            failed = invoke(CLI, "prepare", "--profile", profile)
            self.assertNotEqual(failed.returncode, 0)
            progress = command("prepare", "--profile", profile, "--status")
            self.assertEqual(progress["state"], "failed")
            self.assertEqual(progress["step"], "install")
            source = json.loads(docker("exec", "--user", "abc", name, "cat", "/config/.cache/electivus/downloads/chrome-source.json"))
            artifact = "/config/.cache/electivus/downloads/" + source["sha256"] + ".deb"
            before = docker("exec", name, "stat", "-c", "%Y:%s", artifact)
            docker("exec", name, "chmod", "755", destination)
            prepared = command("prepare", "--profile", profile)
            self.assertEqual(prepared["state"], "completed")
            self.assertEqual(docker("exec", name, "stat", "-c", "%Y:%s", artifact), before)
            self.assertIn("Google Chrome", docker("exec", "--user", "abc", name, "google-chrome", "--version"))
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)

    def test_zsh_is_interactive_and_preserves_customization(self):
        name = "ew-shell-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13408", "--memory", "2560", "--cpus", "2", "--no-shortcut")
            command("start", "--profile", profile)
            self.assertTrue(docker("exec", name, "getent", "passwd", "abc").endswith("/bin/zsh"))
            self.assertEqual(docker("exec", "--user", "abc", name, "zsh", "-c", "printf plain"), "plain")
            probe = "mkdir -p ~/shell-project && cd ~/shell-project && git init -q && touch example.txt && gst --short"
            self.assertIn("?? example.txt", docker("exec", "--user", "abc", name, "zsh", "-ic", probe))
            # A slow user startup command must not make the PTY driver send
            # editing keys before Zsh has entered its line editor.
            docker("exec", "--user", "abc", name, "bash", "-c", "printf '\\nsleep 3\\n' >> ~/.zshrc")
            docker("cp", str(ROOT / "tests/terminal_plugins.py"), name + ":/tmp/terminal_plugins.py")
            plugins = json.loads(docker("exec", "--user", "abc", name, "python3", "/tmp/terminal_plugins.py"))
            self.assertIn("accepted", plugins["autosuggestion"])
            docker("exec", "--user", "abc", name, "bash", "-c", "printf '\\nexport WORKSTATION_PERSONAL=kept\\n' >> ~/.zshrc")
            before = docker("exec", "--user", "abc", name, "sha256sum", "/config/.zshrc")
            command("stop", "--profile", profile)
            docker("container", "rm", name)
            command("start", "--profile", profile)
            self.assertEqual(docker("exec", "--user", "abc", name, "sha256sum", "/config/.zshrc"), before)
            self.assertEqual(docker("exec", "--user", "abc", name, "zsh", "-ic", 'printf "%s" "$WORKSTATION_PERSONAL"'), "kept")
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)

    def test_chrome_preparation_is_observable_and_persistent(self):
        name = "ew-apps-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13407", "--memory", "2560", "--cpus", "2", "--no-shortcut")
            command("start", "--profile", profile)
            progress = command("prepare", "--profile", profile, "--status")
            self.assertIn(progress["state"], {"pending", "running", "failed", "completed"})
            deadline = time.monotonic() + 20
            while progress["state"] == "pending" and time.monotonic() < deadline:
                time.sleep(1)
                progress = command("prepare", "--profile", profile, "--status")
            self.assertNotEqual(progress["state"], "pending", "first desktop session must start preparation automatically")
            prepared = command("prepare", "--profile", profile)
            self.assertEqual(prepared["state"], "completed")
            chrome = prepared["apps"]["chrome"]
            self.assertIn("https://dl.google.com/", chrome["source"])
            self.assertEqual(len(chrome["sha256"]), 64)
            self.assertIn("Google Chrome", docker("exec", "--user", "abc", name, "google-chrome", "--version"))
            rendered = docker("exec", "--user", "abc", name, "timeout", "30", "google-chrome", "--headless",
                              "--disable-gpu", "--dump-dom", "data:text/html,<title>Workstation browser</title><h1>ready</h1>")
            self.assertIn("<h1>ready</h1>", rendered)
            self.assertIn("git version", docker("exec", "--user", "abc", name, "git", "--version"))
            command("stop", "--profile", profile)
            docker("container", "rm", name)
            command("start", "--profile", profile)
            reused = command("prepare", "--profile", profile)
            self.assertEqual(reused["apps"]["chrome"], chrome)
            (profile / "preparation-result.json").write_text(json.dumps(reused, indent=2), encoding="utf-8")
            self.assert_automatic_preparation_checks_manifest(name, profile)
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
