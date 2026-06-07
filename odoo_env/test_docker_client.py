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


class TestExtractCpCommand(unittest.TestCase):
    """Extract usa `docker run --entrypoint cp` (cp DENTRO del contenedor).

    Reemplaza el entrypoint de odoo por cp, asi que odoo NO arranca, y el
    `cp -a` preserva symlinks (docker cp validaba y rompia con babel).
    """

    def setUp(self):
        self.dc = DockerClient()

    def test_extract_cp_command_shape(self):
        result = self.dc.get_extract_cp_command(
            "img", "/usr/lib/python3/dist-packages", "/odoo/ar/14.0e/dist-packages"
        )
        self.assertEqual(
            result,
            [
                "docker",
                "run",
                "--rm",
                "--user",
                "root",
                "--entrypoint",
                "cp",
                "-v",
                "/odoo/ar/14.0e/dist-packages:/oe-extract-dest",
                "img",
                "-a",
                "/usr/lib/python3/dist-packages/.",
                "/oe-extract-dest/",
            ],
        )

    def test_extract_cp_replaces_entrypoint_with_cp(self):
        result = self.dc.get_extract_cp_command("img", "/src", "/host")
        self.assertIn("--entrypoint", result)
        self.assertEqual(result[result.index("--entrypoint") + 1], "cp")

    def test_extract_cp_preserves_symlinks_with_archive_flag(self):
        # `-a` (archive) preserva symlinks tal cual.
        result = self.dc.get_extract_cp_command("img", "/src", "/host")
        self.assertIn("-a", result)

    def test_extract_cp_copies_dir_contents_not_dir(self):
        result = self.dc.get_extract_cp_command("img", "/src/", "/host")
        self.assertIn("/src/.", result)

    def test_extract_cp_mounts_host_dest(self):
        result = self.dc.get_extract_cp_command("img", "/src", "/host")
        self.assertIn("-v", result)
        self.assertIn("/host:/oe-extract-dest", result)
