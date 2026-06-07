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


class TestGetExtractCommand(unittest.TestCase):

    def setUp(self):
        self.dc = DockerClient()

    def test_returns_correct_command_shape(self):
        result = self.dc.get_extract_command("img", "/src", "/host")
        self.assertEqual(
            result,
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "/host:/dest",
                "img",
                "cp",
                "-r",
                "/src/.",
                "/dest/",
            ],
        )

    def test_no_entrypoint_flag(self):
        result = self.dc.get_extract_command("img", "/src", "/host")
        self.assertNotIn("--entrypoint", result)

    def test_no_interactive_flag(self):
        result = self.dc.get_extract_command("img", "/src", "/host")
        self.assertNotIn("-it", result)

    def test_image_token_before_cp(self):
        result = self.dc.get_extract_command("img", "/src", "/host")
        img_idx = result.index("img")
        cp_idx = result.index("cp")
        self.assertLess(img_idx, cp_idx)
