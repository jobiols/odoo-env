import unittest
from unittest.mock import patch

from odoo_env.command import Command, EnsureNetworkCommand
from odoo_env.config import OeConfig
from odoo_env.constants import (
    DBTOOLS_IMAGE,
)
from odoo_env.odooenv import OdooEnv
from odoo_env.repos import GitRepo
from odoo_env.singleton import SingletonMeta


class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        # Add default values for all possible args used in code
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

TEST2_CLIENT_MANIFEST = {
    "name": "test2_client",
    "version": "9.0.3.0.0",
    "odoo-license": "CE",
    "env-ver": "2",
    "docker-images": [
        "odoo jobiols/odoo-jeo:9.0",
        "postgres postgres:11.1-alpine",
        "aeroo adhoc/aeroo",
        "nginx nginx",
    ],
    "git-repos": [
        "https://github.com/jobiols/odoo-addons.git",
        "https://github.com/ingadhoc/odoo-argentina.git adhoc-odoo-argentina",
    ],
}

TEST2E_CLIENT_MANIFEST = {
    "name": "test2e_client",
    "version": "9.0.3.0.0",
    "odoo-license": "EE",
    "env-ver": "2",
    "docker-images": [
        "odoo jobiols/odoo-jeo:9.0",
        "postgres postgres:11.1-alpine",
    ],
    "git-repos": ["https://github.com/jobiols/odoo-enterprise.git"],
}


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        # Reset Singleton for each test
        if OeConfig in SingletonMeta._instances:
            del SingletonMeta._instances[OeConfig]

        # Patch Config to avoid reading/writing real user config
        self.config_data_patcher = patch("odoo_env.config.OeConfig._get_config_data")
        self.mock_config_data = self.config_data_patcher.start()
        self.mock_config_data.return_value = {
            "clients": [
                {"test_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
                {"test2_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
                {"test2e_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
            ],
            "client": "test_client",
            "environment": "prod",
            "base_dir": "/odoo_ar/",
            "last_version_check": "2026-04-05",
        }

        self.save_config_patcher = patch("odoo_env.config.OeConfig._save_config_data")
        self.mock_save_config = self.save_config_patcher.start()

        # Patch Manifest
        self.patcher = patch("odoo_env.client.Client.get_manifest")
        self.mock_get_manifest = self.patcher.start()
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST

    def tearDown(self):
        self.patcher.stop()
        self.config_data_patcher.stop()
        self.save_config_patcher.stop()

    def test_install(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(
            debug=False, no_repos=False, nginx=True, client="test_client"
        )
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir (index 1 in new structure)
        psql_dir = f"{OeConfig().base_dir}odoo-9.0/test_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_install2(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST2_CLIENT_MANIFEST
        options = MockArgs(
            debug=False, no_repos=False, nginx=True, client="test2_client"
        )
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir
        psql_dir = f"{OeConfig().base_dir}odoo-9.0/test2_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_install2_enterprise(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST2E_CLIENT_MANIFEST
        options = MockArgs(
            debug=True,
            no_repos=False,
            nginx=True,
            extract_sources=False,
            client="test2e_client",
        )
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir
        psql_dir = f"{OeConfig().base_dir}odoo-9.0e/test2e_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_cmd(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(
            debug=False, no_repos=False, nginx=False, client="test_client"
        )
        oe = OdooEnv(options)
        c = Command(oe, command="cmd", usr_msg="hola")
        self.assertEqual(c.command, "cmd")

    def test_qa(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        modules = "modulo_a_testear"
        oe = OdooEnv(options)
        cmds = oe.qa(modules)

        # Order: volumes, env, links, image
        command = [
            "docker",
            "run",
            "--rm",
            "-it",
            "--network",
            "odoo-net",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "WDB_SOCKET_SERVER=wdb",
            "-e",
            "WDB_NO_BROWSER_AUTO_OPEN=True",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:9.0",
            "--stop-after-init",
            "--log-level=test",
            "--test-enable",
            "-d",
            "test_client_test",
            "-u",
            "modulo_a_testear",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_run_cli(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, nginx=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.run_client()

        command = [
            "docker",
            "run",
            "-d",
            "--name",
            "test_client",
            "--network",
            "odoo-net",
            "--restart",
            "unless-stopped",
            "-p",
            "8069:8069",
            "-p",
            "8072:8072",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "aeroo:aeroo",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:9.0",
            "--logfile=/var/log/odoo/odoo.log",
            "-d",
            "test_client_prod",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_pull_images(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, nginx=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        self.assertEqual(cmds[0].command, ["docker", "run", "jobiols/odoo-jeo:9.0"])

    def test_update(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, nginx=False, client="test_client")
        database = "test_client_prod"
        modules = ["all"]
        oe = OdooEnv(options)
        cmds = oe.update(database, modules)

        command = [
            "docker",
            "run",
            "--rm",
            "-it",
            "--network",
            "odoo-net",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:9.0",
            "--stop-after-init",
            "--logfile=false",
            "-d",
            "test_client_prod",
            "-u",
            "all",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_restore(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, nginx=False, client="test_client")
        database = "test_client_prod"
        backup_file = "bkp.zip"
        oe = OdooEnv(options)
        cmds = oe.restore("test_client", database, backup_file, no_deactivate=False)

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "odoo-net",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/backup_dir/:/backup:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/test_client/data_dir/filestore:/filestore:rw",
            "-e",
            "NEW_DBNAME=test_client_prod",
            "-e",
            "ZIPFILE=bkp.zip",
            "-e",
            "DEACTIVATE=True",
            DBTOOLS_IMAGE,
        ]
        self.assertEqual(cmds[0].command, command)

    def test_download_image_sources(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        # Force debug mode in mock config data
        self.mock_config_data.return_value["environment"] = "debug"

        options = MockArgs(
            debug=True,
            no_repos=False,
            nginx=False,
            extract_sources=True,
            client="test_client",
        )
        oe = OdooEnv(options)
        cmds = oe.install()
        # Find the extract command in the list (look for dist-packages)
        extract_cmd = next(
            (
                c
                for c in cmds
                if c._usr_msg and "Extracting dist-packages" in c._usr_msg
            ),
            None,
        )

        command = [
            "docker",
            "run",
            "--rm",
            "-it",
            "--entrypoint",
            "/extract_dist-packages.sh",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/dist-packages/:/mnt/dist-packages:rw",
            "jobiols/odoo-jeo:9.0.debug",
        ]
        self.assertEqual(extract_cmd.command, command)

    def test_check_version(self):
        options = MockArgs(debug=False, client="test_client")
        OeConfig(options)
        self.assertIsNone(OeConfig().check_version())

    def test_environment(self):
        options = MockArgs(debug=False, client="test_client")
        OeConfig(options)
        # env = OeConfig().get_environment()
        OeConfig().save_environment("prod")
        self.assertEqual(OeConfig().prod, True)
        OeConfig().save_environment("debug")
        self.assertEqual(OeConfig().debug, True)

    def test_save_multiple_clients(self):
        options = MockArgs(debug=False, client="test_client")
        OeConfig(options)
        OeConfig().save_client_path("test_clientx", "multiple_path1")
        OeConfig().save_client_path("test_clientx", "multiple_path2")
        self.assertEqual(
            str(OeConfig().get_client_path("test_clientx")), "multiple_path1"
        )

    def test_repo_clone(self):
        repo = GitRepo("https://github.com/jobiols/project.git", "9.0")
        self.assertEqual(
            repo.clone, "clone --depth 1  -b 9.0 https://github.com/jobiols/project.git"
        )

    def test_repo2_clone(self):
        repo = GitRepo("https://github.com/jobiols/project.git", "9.0")
        self.assertEqual(repo.dir_name, "project")

    def test_ensure_network_skips_when_exists(self):
        """SC-03: check_args() returns False when docker network inspect exits 0."""
        import subprocess as _subprocess

        mock_parent = unittest.mock.MagicMock()
        mock_parent.verbose = False

        cmd = EnsureNetworkCommand(
            mock_parent,
            command=["docker", "network", "create", "odoo-net"],
            usr_msg="Starting odoo-net network if needed",
            args="odoo-net",
        )

        mock_result = unittest.mock.MagicMock()
        mock_result.returncode = 0

        with patch("odoo_env.command.subprocess.run", return_value=mock_result) as mock_run:
            result = cmd.check_args()

        self.assertFalse(result)
        mock_run.assert_called_once_with(
            ["docker", "network", "inspect", "odoo-net"],
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )

    def test_ensure_network_runs_when_absent(self):
        """SC-04: check_args() returns True when docker network inspect exits non-zero."""
        import subprocess as _subprocess

        mock_parent = unittest.mock.MagicMock()
        mock_parent.verbose = False

        cmd = EnsureNetworkCommand(
            mock_parent,
            command=["docker", "network", "create", "odoo-net"],
            usr_msg="Starting odoo-net network if needed",
            args="odoo-net",
        )

        mock_result = unittest.mock.MagicMock()
        mock_result.returncode = 1

        with patch("odoo_env.command.subprocess.run", return_value=mock_result) as mock_run:
            result = cmd.check_args()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["docker", "network", "inspect", "odoo-net"],
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )
