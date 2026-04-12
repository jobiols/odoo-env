import unittest

from odoo_env.services.docker_client import DockerClient


class TestDockerClient(unittest.TestCase):
    def test_get_pull_command_returns_docker_pull_image(self):
        dc = DockerClient()
        result = dc.get_pull_command("postgres:17.5-alpine")
        self.assertEqual(result, ["docker", "pull", "postgres:17.5-alpine"])

    def test_get_pull_command_does_not_contain_run(self):
        dc = DockerClient()
        result = dc.get_pull_command("postgres:17.5-alpine")
        self.assertNotIn("run", result)

    def test_get_pull_command_has_no_flags(self):
        dc = DockerClient()
        result = dc.get_pull_command("some-image:tag")
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["docker", "pull", "some-image:tag"])
