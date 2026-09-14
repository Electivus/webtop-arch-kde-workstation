"""Compose builds and writes a Linux project through the notebook's engine."""
import json
import os
import subprocess
import unittest
import uuid

from test_commands import ROOT, command, docker

IMAGE = os.environ.get("WORKSTATION_TEST_IMAGE", "electivus/webtop-arch-kde-base:t04")


class DockerProjectsAcceptance(unittest.TestCase):
    def test_project_build_mount_write_and_recreation(self):
        name = "ew-compose-" + uuid.uuid4().hex[:10]
        profile = ROOT / ".local" / name
        project = "/config/projects/compose example"

        def compose(*args):
            return docker("exec", "--user", "abc", "--env", "COMPOSE_PROJECT_NAME=" + name,
                          "--env", "WORKSTATION_PROJECT_SUBPATH=compose example", "--workdir", project,
                          name, "docker", "compose", *args)

        try:
            host_engine = json.loads(docker("info", "--format", "{{json .}}"))["ID"]
            command("install", "--profile", profile, "--name", name, "--image", IMAGE,
                    "--port", "13412", "--memory", "2560", "--cpus", "2", "--no-shortcut")
            first = command("start", "--profile", profile)
            connection = json.loads(docker("exec", "--user", "abc", name, "workstation-docker-check"))
            self.assertEqual(connection["engineId"], host_engine)
            self.assertEqual(connection["homeVolume"], name + "-home")
            docker("exec", "--user", "abc", name, "cp", "-r", "/etc/electivus/examples/compose-demo", project)
            docker("exec", "--user", "abc", name, "python3", "-c", r"""
from pathlib import Path
import sys
project = Path(sys.argv[1])
script = project / 'write-result.sh'
script.write_text(script.read_text().replace('worker:', 'local-build:'))
(project / 'input.txt').write_text('primeira ação\n')
""", project)
            validation = json.loads(docker("exec", "--user", "abc", name, "workstation-docker-check", project))
            self.assertEqual(validation["projectSubpath"], "projects/compose example")
            compose("up", "--detach", "--build", "--wait", "--wait-timeout", "40")
            self.assertEqual(docker("exec", "--user", "abc", name, "cat", project + "/result.txt"),
                             "local-build: primeira ação")
            service = compose("ps", "--quiet", "writer")
            mounts = json.loads(docker("inspect", service))[0]["Mounts"]
            self.assertTrue(any(mount["Name"] == name + "-home" and mount["Destination"] == "/workspace"
                                for mount in mounts if mount["Type"] == "volume"))
            compose("down")
            command("stop", "--profile", profile)
            docker("container", "rm", name)
            second = command("start", "--profile", profile)
            self.assertNotEqual(first["containerId"], second["containerId"])
            docker("exec", "--user", "abc", name, "python3", "-c",
                   "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('segunda ação\\n')",
                   project + "/input.txt")
            compose("up", "--detach", "--build", "--wait", "--wait-timeout", "40")
            self.assertEqual(docker("exec", "--user", "abc", name, "cat", project + "/result.txt"),
                             "local-build: segunda ação")
            unavailable = subprocess.run(["docker", "exec", "--user", "abc", name, "workstation-docker-check",
                                          "/config/projects/missing"], capture_output=True, text=True)
            self.assertNotEqual(unavailable.returncode, 0)
            self.assertIn("Project directory does not exist", unavailable.stderr)
            disconnected = subprocess.run(["docker", "exec", "--user", "abc", "--env",
                                           "DOCKER_HOST=unix:///tmp/unavailable-docker.sock", name,
                                           "workstation-docker-check"], capture_output=True, text=True)
            self.assertNotEqual(disconnected.returncode, 0)
            self.assertIn("Docker engine is unavailable", disconnected.stderr)
            compose("down", "--rmi", "all")
            (profile / "compose-result.json").write_text(json.dumps({
                "engine": connection, "project": validation, "builtFromLocalContext": True,
                "serviceWroteProject": True, "survivedRecreation": True,
                "missingPathDiagnosed": True, "unavailableEngineDiagnosed": True,
            }, indent=2), encoding="utf-8")
        finally:
            services = subprocess.run(["docker", "ps", "--all", "--quiet", "--filter",
                                       "label=com.docker.compose.project=" + name], capture_output=True, text=True)
            for service in services.stdout.split():
                subprocess.run(["docker", "container", "rm", "--force", service], capture_output=True)
            subprocess.run(["docker", "image", "rm", name + "-writer:local"], capture_output=True)
            subprocess.run(["docker", "container", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", name + "-home"], capture_output=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
