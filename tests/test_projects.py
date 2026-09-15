"""Persistent Linux projects and host exchange through the delivered commands."""
import json
import os
from pathlib import Path
import subprocess
import unittest
import uuid

from test_commands import ROOT, CLI, command, docker, invoke

IMAGE = os.environ.get("WORKSTATION_TEST_IMAGE", "electivus/webtop-arch-kde-base:t04")
EXCHANGE_DIRECTORY = Path(os.environ.get("WORKSTATION_TEST_EXCHANGE_DIRECTORY", str(ROOT / ".local" / "exchange")))


class ProjectsAcceptance(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Docker Desktop Windows file sharing")
    def test_unshared_exchange_is_reported_before_start(self):
        name = "ew-unshared-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        exchange = profile / "unshared"
        exchange.mkdir(parents=True)
        settings = json.loads((Path(os.environ["APPDATA"]) / "Docker/settings-store.json").read_text(encoding="utf-8-sig"))
        if not (settings.get("UseLibkrun") or settings.get("WslEngineEnabled") is False):
            self.skipTest("This backend does not require explicit Windows directory sharing")
        for shared in settings.get("FilesharingDirectories", []):
            try:
                exchange.resolve().relative_to(Path(shared).resolve())
            except ValueError:
                continue
            self.skipTest("The operator already shared a parent of the negative fixture")
        result = invoke(CLI, "install", "--profile", profile, "--name", name, "--image", IMAGE,
                        "--memory", "2560", "--cpus", "2", "--no-shortcut", "--exchange", exchange)
        self.assertNotEqual(result.returncode, 0, "detect sharing prerequisite before requesting a Docker mount")
        self.assertIn("File sharing", result.stderr)
        self.assertIn(str(exchange), result.stderr)
        self.assertFalse((profile / "profile.json").exists())

    def test_linux_project_and_bidirectional_exchange_survive_recreation(self):
        name = "ew-project-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        exchange = EXCHANGE_DIRECTORY / name / "troca com Windows, ação"
        exchange.mkdir(parents=True)
        # The CI runner UID differs from the desktop UID. Only this disposable
        # exchange directory is made writable to both users.
        if os.name != "nt":
            exchange.chmod(0o777)
        (exchange / "from-windows.txt").write_text("Windows: ação\n", encoding="utf-8")
        if os.name != "nt":
            (exchange / "from-windows.txt").chmod(0o666)
        try:
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13411", "--memory", "2560", "--cpus", "2", "--no-shortcut",
                    "--exchange", exchange)
            first = command("start", "--profile", profile)
            self.assertEqual(first["storage"]["projects"], "/config/projects")
            self.assertEqual(first["storage"]["exchange"], str(exchange.resolve()))
            docker("exec", "--user", "abc", name, "python3", "-c", r"""
from pathlib import Path
import os
project = Path('/config/projects/ação com espaços')
project.mkdir()
(project / 'Readme').write_text('upper\n')
(project / 'readme').write_text('lower\n')
(project / 'run.sh').write_text('#!/bin/sh\nprintf project-ok\n')
(project / 'run.sh').chmod(0o751)
(project / 'run-link').symlink_to('run.sh')
assert Path('/exchange/from-windows.txt').read_text() == 'Windows: ação\n'
Path('/exchange/from-windows.txt').write_text('Linux editou\n')
Path('/exchange/from-linux.txt').write_text('Linux: coração\n')
Path('/exchange/from-linux.txt').chmod(0o666)
""")
            self.assertEqual((exchange / "from-windows.txt").read_text(encoding="utf-8"), "Linux editou\n")
            self.assertEqual((exchange / "from-linux.txt").read_text(encoding="utf-8"), "Linux: coração\n")
            (exchange / "from-linux.txt").write_text("Windows editou\n", encoding="utf-8")
            command("stop", "--profile", profile)
            docker("container", "rm", name)
            second = command("start", "--profile", profile)
            self.assertNotEqual(first["containerId"], second["containerId"])
            self.assertEqual(first["homeVolume"], second["homeVolume"])
            proof = json.loads(docker("exec", "--user", "abc", name, "python3", "-c", r"""
from pathlib import Path
import json, os, stat, subprocess
project = Path('/config/projects/ação com espaços')
assert (project / 'Readme').read_text() == 'upper\n'
assert (project / 'readme').read_text() == 'lower\n'
assert stat.S_IMODE((project / 'run.sh').stat().st_mode) == 0o751
assert (project / 'run.sh').stat().st_uid == os.getuid()
assert os.readlink(project / 'run-link') == 'run.sh'
assert subprocess.check_output([str(project / 'run-link')], text=True) == 'project-ok'
assert Path('/exchange/from-linux.txt').read_text() == 'Windows editou\n'
assert Path('/config/WindowsExchange').resolve() == Path('/exchange')
print(json.dumps({'caseSensitiveNames': True, 'mode': '0751', 'symlink': 'run.sh',
                  'executableResult': 'project-ok', 'exchange': 'bidirectional'}))
"""))
            (profile / "projects-result.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
        finally:
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
