"""Salesforce acceptance through the delivered commands and editor interfaces."""
import json
import os
import subprocess
import sys
import time
import unittest
import uuid

from test_commands import ROOT, command, docker

IMAGE = os.environ.get("WORKSTATION_SALESFORCE_TEST_IMAGE", "electivus/webtop-arch-kde-salesforce:t03")


class SalesforceAcceptance(unittest.TestCase):
    def test_editor_download_resumes_after_container_interruption(self):
        name = "ew-sf-retry-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13412", "--memory", "6144", "--cpus", "4", "--no-shortcut")
            command("start", "--profile", profile)
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                progress = command("prepare", "--profile", profile, "--status")
                if progress.get("app") == "code-insiders" and progress["step"] == "download" and progress.get("bytes", 0) > 0:
                    break
                self.assertNotIn(progress["state"], {"failed", "completed"}, progress)
                time.sleep(0.15)
            else:
                self.fail("Insiders download did not start")
            completed = {app: progress["apps"][app] for app in ("chrome", "code")}
            docker("kill", name)
            inspect_partial = """
import json
from pathlib import Path
root = Path('/config')
cache = root / '.cache/electivus/downloads'
manifest = json.loads((cache / 'code-insiders-source.json').read_text())
files = [cache / (manifest['sha256'] + suffix) for suffix in ('.part', '.deb')]
artifact = next(path for path in files if path.exists())
assert not (root / '.local/share/electivus/apps/code-insiders/current').exists()
print(json.dumps({'bytes': artifact.stat().st_size, 'size': manifest['size'], 'artifact': artifact.name}))
"""
            interrupted = json.loads(docker("run", "--rm", "--entrypoint", "python3",
                                            "--mount", "type=volume,src=" + name + "-home,dst=/config",
                                            IMAGE, "-c", inspect_partial))
            self.assertGreater(interrupted["bytes"], 0)
            self.assertLessEqual(interrupted["bytes"], interrupted["size"])
            command("start", "--profile", profile)
            prepared = command("prepare", "--profile", profile)
            self.assertEqual(prepared["state"], "completed")
            for app, receipt in completed.items():
                self.assertEqual(prepared["apps"][app], receipt)
            self.assertIn("1.", docker("exec", "--user", "abc", name, "code-insiders", "--version"))
            (profile / "interruption-result.json").write_text(
                json.dumps({"interrupted": interrupted, "preparation": prepared}, indent=2), encoding="utf-8")
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)

    def test_both_official_editors_and_cli_survive_recreation(self):
        name = "ew-sf-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13410", "--memory", "6144", "--cpus", "4", "--no-shortcut")
            command("start", "--profile", profile)
            prepared = command("prepare", "--profile", profile)
            self.assertEqual(prepared["state"], "completed")
            self.assertEqual(set(prepared["apps"]), {"chrome", "code", "code-insiders", "salesforce-cli", "extensions"})
            for editor in ("code", "code-insiders"):
                self.assertTrue(prepared["apps"][editor]["source"].startswith("https://packages.microsoft.com/repos/code/"))
                self.assertEqual(len(prepared["apps"][editor]["sha256"]), 64)
                self.assertIn(prepared["apps"][editor]["version"].split("-")[0],
                              docker("exec", "--user", "abc", name, editor, "--version"))
                installed = docker("exec", "--user", "abc", name, editor, "--list-extensions", "--show-versions")
                self.assertIn("salesforce.salesforcedx-vscode@", installed)
                self.assertIn("salesforce.salesforcedx-vscode-apex@", installed)
            self.assertTrue(docker("exec", "--user", "abc", name, "node", "--version").startswith("v24."))
            self.assertIn("21.", docker("exec", "--user", "abc", name, "java", "--version"))
            generated = json.loads(docker("exec", "--user", "abc", name, "sf", "project", "generate",
                                          "--name", "sample", "--output-dir", "/config/projects", "--json"))
            self.assertEqual(generated["status"], 0)
            docker("exec", "--user", "abc", name, "python3", "-c",
                   "from pathlib import Path; Path('/config/projects/sample.code-workspace').write_text('{\"folders\":[{\"path\":\"sample\"}]}')")
            # docker exec does not inherit Plasma's desktop detection variables.
            # Use the delivered KDE backend, as the graphical file manager does.
            kde = ("exec", "--user", "abc", name, "env", "XDG_CURRENT_DESKTOP=KDE", "KDE_SESSION_VERSION=6")
            self.assertEqual(docker(*kde, "xdg-mime", "query", "default", "text/plain"), "code-insiders.desktop")
            self.assertEqual(docker(*kde, "xdg-mime", "query", "default", "application/x-code-workspace"), "code-insiders.desktop")
            self.assertEqual(docker(*kde, "xdg-mime", "query", "filetype", "/config/projects/sample.code-workspace"),
                             "application/x-code-workspace")
            command("stop", "--profile", profile)
            docker("container", "rm", name)
            command("start", "--profile", profile)
            reused = command("prepare", "--profile", profile)
            self.assertEqual(reused["apps"], prepared["apps"])
            docker("exec", "--user", "abc", name, "test", "-f", "/config/projects/sample/sfdx-project.json")
            docker("cp", str(ROOT / "tests/editor_probe"), name + ":/config/editor_probe")
            for editor in ("code", "code-insiders"):
                docker("cp", str(ROOT / "tests/salesforce_sample") + "/.", name + ":/config/projects/sample")
                docker("exec", name, "chown", "-R", "1000:1000", "/config/editor_probe", "/config/projects/sample")
                receipt = "/config/" + editor + "-services.json"
                exercised = subprocess.run(
                    ["docker", "exec", "--user", "abc", "--env", "ELECTIVUS_TEST_RESULT=" + receipt,
                     name, "timeout", "300", editor, "--wait", "--new-window", "--verbose", "--disable-workspace-trust",
                     "--skip-welcome", "--skip-release-notes", "--extensionDevelopmentPath=/config/editor_probe",
                     "--extensionTestsPath=/config/editor_probe/index.js", "/config/projects/sample"],
                    text=True, encoding="utf-8", capture_output=True, timeout=330)
                (profile / (editor + "-services.log")).write_text(exercised.stdout + exercised.stderr, encoding="utf-8")
                copied = subprocess.run(["docker", "cp", name + ":" + receipt, str(profile / (editor + "-services.json"))],
                                        text=True, capture_output=True)
                self.assertEqual(copied.returncode, 0, "Editor produced no service result. See " + str(profile / (editor + "-services.log")))
                services = json.loads((profile / (editor + "-services.json")).read_text())
                self.assertEqual(exercised.returncode, 0, exercised.stdout + exercised.stderr)
                self.assertEqual(services["result"], "passed")
            (profile / "salesforce-result.json").write_text(json.dumps(reused, indent=2), encoding="utf-8")
        finally:
            if os.environ.get("WORKSTATION_KEEP_FAILED") and sys.exc_info()[0]:
                print("Retained failed fixture for diagnosis:", profile, file=sys.stderr)
            else:
                subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
                subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
