import unittest
from unittest.mock import patch

from odoo_env.config import OeConfig


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
            "restore": False,
            "create_test_db": False,
            "no_deactivate": False,
            "database": None,
            "module": None,
            "backup_file": None,
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
        "aeroo jobiols/aeroo-docs",
    ],
    "git-repos": [
        "https://github.com/jobiols/cl-test-client.git",
        "https://github.com/jobiols/odoo-addons.git",
    ],
    "env-ver": "2",
}


class OdooEnvTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        OeConfig.reset()

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
        OeConfig.reset()
