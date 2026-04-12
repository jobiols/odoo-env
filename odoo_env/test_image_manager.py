import unittest
from unittest.mock import patch

from odoo_env.config import OeConfig
from odoo_env.singleton import SingletonMeta
from odoo_env.odooenv import OdooEnv


class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        defaults = {
            "debug": False,
            "prod": False,
            "client": None,
            "base_dir": None,
            "install": False,
            "run_env": False,
            "pull_images": False,
            "write_config": False,
            "run_cli": False,
            "stop_env": False,
            "stop_cli": False,
            "update": False,
            "deploy_keys": False,
            "modules_to_test": None,
            "server_help": False,
            "backup_list": False,
            "restore": False,
            "create_test_db": False,
            "force_create": False,
            "no_deactivate": False,
            "from_prod": False,
            "no_repos": False,
            "database": None,
            "module": None,
            "backup_file": None,
            "nginx": False,
        }
        for k, v in defaults.items():
            if k not in self.__dict__:
                setattr(self, k, v)


TEST_CLIENT_MANIFEST = {
    "name": "test_client",
    "version": "9.0.1.0.0",
    "docker-images": [
        "odoo jobiols/odoo-jeo:9.0",
        "postgres postgres:9.5",
        "nginx nginx:latest",
        "aeroo jobiols/aeroo-docs",
    ],
    "git-repos": [
        "https://github.com/jobiols/cl-test-client.git",
        "https://github.com/jobiols/odoo-addons.git",
    ],
    "env-ver": "2",
}


class TestImageManager(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        if OeConfig in SingletonMeta._instances:
            del SingletonMeta._instances[OeConfig]

        self.config_data_patcher = patch("odoo_env.config.OeConfig._get_config_data")
        self.mock_config_data = self.config_data_patcher.start()
        self.mock_config_data.return_value = {
            "clients": [
                {"test_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
            ],
            "client": "test_client",
            "environment": "prod",
            "base_dir": "/odoo_ar/",
            "last_version_check": "2026-04-05",
        }

        self.save_config_patcher = patch("odoo_env.config.OeConfig._save_config_data")
        self.mock_save_config = self.save_config_patcher.start()

        self.patcher = patch("odoo_env.client.Client.get_manifest")
        self.mock_get_manifest = self.patcher.start()
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST

    def tearDown(self):
        self.patcher.stop()
        self.config_data_patcher.stop()
        self.save_config_patcher.stop()

    def test_pull_images_uses_pull_not_run(self):
        with patch(
            "odoo_env.services.docker_client.DockerClient.get_pull_command",
            return_value=["docker", "pull", "jobiols/odoo-jeo:9.0"],
        ) as mock_pull, patch(
            "odoo_env.services.docker_client.DockerClient.get_run_command"
        ) as mock_run:
            options = MockArgs(debug=False, client="test_client")
            oe = OdooEnv(options)
            oe.pull_images()
            mock_pull.assert_called()
            mock_run.assert_not_called()

    def test_pull_images_command_starts_with_docker_pull(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        self.assertEqual(cmds[0].command[:2], ["docker", "pull"])

    def test_pull_images_calls_extract_sources_in_debug_mode(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        has_rm = any("rm" in c.command for c in cmds)
        self.assertTrue(has_rm, "Expected extract_sources rm commands in debug mode")

    def test_pull_images_no_extract_sources_in_non_debug_mode(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        for c in cmds:
            self.assertNotIn(
                "rm",
                c.command,
                f"Unexpected rm command in non-debug pull_images: {c.command}",
            )
            self.assertFalse(
                c.command and c.command[0] == "mkdir",
                f"Unexpected mkdir command in non-debug pull_images: {c.command}",
            )
