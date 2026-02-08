import unittest
from unittest.mock import patch

from odoo_env.command import Command
from odoo_env.config import OeConfig
from odoo_env.constants import (
    OeConfig().base_dir,
    DBTOOLS_IMAGE,
)
from odoo_env.odooenv import OdooEnv
from odoo_env.repos import GitRepo

TEST_CLIENT_MANIFEST = {
    "name": "test_client",
    "version": "9.0.1.0",
    "docker": [
        {"name": "odoo", "usr": "jobiols", "img": "odoo-jeo", "ver": "9.0"},
        {"name": "postgres", "usr": "postgres", "ver": "9.5"},
        {"name": "nginx", "usr": "nginx", "ver": "latest"},
        {"name": "aeroo", "usr": "jobiols", "img": "aeroo-docs"},
    ],
    "repos": [
        {"usr": "jobiols", "repo": "cl-test-client", "branch": "9.0"},
        {"usr": "jobiols", "repo": "odoo-addons", "branch": "9.0"},
    ],
    "env-ver": "1",
}

TEST2_CLIENT_MANIFEST = {
    "name": "test2_client",
    "version": "9.0.3.0",
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
    "version": "9.0.3.0",
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
        self.patcher = patch("odoo_env.client.Client.get_manifest")
        self.mock_get_manifest = self.patcher.start()
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST

    def tearDown(self):
        self.patcher.stop()

    def test_install(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False, "no-repos": False, "nginx": True}
        oe = OdooEnv(options)
        cmds = oe.install("test_client")
        self.assertEqual(cmds[0].command, ["sudo", "mkdir", "-p", OeConfig().base_dir])
        self.assertEqual(
            cmds[2].command,
            [
                "sudo",
                "mkdir",
                "-p",
                f"{OeConfig().base_dir}odoo-9.0/test_client/postgresql",
            ],
        )

    def test_install2(self):
        self.mock_get_manifest.side_effect = lambda path: TEST2_CLIENT_MANIFEST
        options = {"debug": False, "no-repos": False, "nginx": True}
        oe = OdooEnv(options)
        cmds = oe.install("test2_client")
        self.assertEqual(cmds[0].command, ["sudo", "mkdir", "-p", OeConfig().base_dir])
        self.assertEqual(
            cmds[2].command,
            [
                "sudo",
                "mkdir",
                "-p",
                f"{OeConfig().base_dir}odoo-9.0/test2_client/postgresql",
            ],
        )

    def test_install2_enterprise(self):
        self.mock_get_manifest.side_effect = lambda path: TEST2E_CLIENT_MANIFEST
        options = {
            "debug": True,
            "no-repos": False,
            "nginx": True,
            "extract_sources": False,
        }
        oe = OdooEnv(options)
        cmds = oe.install("test2e_client")
        self.assertEqual(cmds[0].command, ["sudo", "mkdir", "-p", OeConfig().base_dir])
        self.assertEqual(
            cmds[2].command,
            [
                "sudo",
                "mkdir",
                "-p",
                f"{OeConfig().base_dir}odoo-9.0e/test2e_client/postgresql",
            ],
        )

    def test_cmd(self):
        options = {"debug": False, "no-repos": False, "nginx": False}
        oe = OdooEnv(options)
        c = Command(oe, command="cmd", usr_msg="hola")
        self.assertEqual(c.command, "cmd")

    def test_qa(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False}
        client_name = "test_client"
        database = "cliente_test"
        modules = "modulo_a_testear"
        oe = OdooEnv(options)
        cmds = oe.qa(client_name, database, modules)

        # Order: run, --rm, -it, --network, volumes, env, links, image, stop-after-init, log-level,
        # test-enable, extra_args
        command = [
            "sudo",
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
            "jobiols/odoo-jeo:9.0",  # Expect non-debug image for v1
            "--stop-after-init",
            "--log-level=test",
            "--test-enable",
            "-d",
            "cliente_test",
            "-u",
            "modulo_a_testear",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_run_cli(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False, "nginx": False}
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.run_client(client_name)

        # Order: run, -d, --name, --network, --restart, -p, -v, -e, --link, image, --logfile
        command = [
            "sudo",
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
        ]
        self.assertEqual(cmds[0].command, command)

    def test_pull_images(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False, "nginx": False}
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.pull_images(client_name)
        # Expect odoo first as per manifest
        self.assertEqual(
            cmds[0].command, ["sudo", "docker", "pull", "jobiols/odoo-jeo:9.0"]
        )

    def test_update(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False, "nginx": False}
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.update(client_name, "client_prod", ["all"])

        # Order: run, --rm, -it, --network, -v, -e, --link, image, --stop-after-init, --logfile, extra_args
        command = [
            "sudo",
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
            "client_prod",
            "-u",
            "all",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_restore(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {"debug": False, "nginx": False}
        client_name = "test_client"
        database = "client_prod"
        backup_file = "bkp.zip"
        oe = OdooEnv(options)
        cmds = oe.restore(client_name, database, backup_file, no_deactivate=False)

        # Order: run, --rm, --network, -v, -e, image
        command = [
            "sudo",
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
            "NEW_DBNAME=client_prod",
            "-e",
            "ZIPFILE=bkp.zip",
            "-e",
            "DEACTIVATE=True",
            DBTOOLS_IMAGE,
        ]
        self.assertEqual(cmds[0].command, command)

    def test_download_image_sources(self):
        self.mock_get_manifest.side_effect = lambda path: TEST_CLIENT_MANIFEST
        options = {
            "debug": True,
            "no-repos": False,
            "nginx": False,
            "extract_sources": True,
        }
        oe = OdooEnv(options)
        cmds = oe.install("test_client")
        self.assertEqual(cmds[0].command, ["sudo", "mkdir", "-p", OeConfig().base_dir])

        # Order: run, --rm, -it, --entrypoint, -v, image
        command = [
            "sudo",
            "docker",
            "run",
            "--rm",
            "-it",
            "--entrypoint",
            "/extract_dist-packages.sh",
            "-v",
            f"{OeConfig().base_dir}odoo-9.0/dist-packages/:/mnt/dist-packages:rw",
            "jobiols/odoo-jeo:9.0",
        ]
        self.assertEqual(cmds[25].command, command)

    def test_check_version(self):
        self.assertTrue(OeConfig().check_version())

    def test_environment(self):
        env = OeConfig().get_environment()
        OeConfig().save_environment("prod")
        env = OeConfig().get_environment()
        self.assertEqual(env, "prod")
        OeConfig().save_environment("debug")
        env = OeConfig().get_environment()
        self.assertEqual(env, "debug")

    def test_save_multiple_clients(self):
        OeConfig().save_client_path("test_clientx", "multiple_path1")
        OeConfig().save_client_path("test_clientx", "multiple_path2")
        self.assertEqual(OeConfig().get_client_path("test_clientx"), "multiple_path1")

    def test_repo_clone(self):
        repo = GitRepo({"usr": "jobiols", "repo": "project", "branch": "9.0"})
        self.assertEqual(
            repo.clone, "clone --depth 1 -b 9.0 https://github.com/jobiols/project"
        )

    def test_repo2_clone(self):
        repo = GitRepo("https://github.com/jobiols/project.git", "9.0")
        self.assertEqual(repo.dir_name, "project")
