import subprocess
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

from odoo_env.command import Command, EnsureNetworkCommand
from odoo_env.config import OeConfig
from odoo_env.constants import (
    DBTOOLS_IMAGE,
    WDB_IMAGE_DEFAULT,
)
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.messages import OeError
from odoo_env.odooenv import OdooEnv
from odoo_env.repos import GitRepo
from odoo_env.test_helpers import TEST_CLIENT_MANIFEST, MockArgs, OdooEnvTestCase

TEST2_CLIENT_MANIFEST = {
    "name": "test2_client",
    "version": "14.0.3.0.0",
    "odoo-license": "CE",
    "env-ver": "2",
    "docker-images": [
        "odoo jobiols/odoo-jeo:14.0",
        "postgres postgres:13",
        "aeroo adhoc/aeroo",
    ],
    "git-repos": [
        "https://github.com/jobiols/odoo-addons.git",
        "https://github.com/ingadhoc/odoo-argentina.git adhoc-odoo-argentina",
    ],
}

TEST2E_CLIENT_MANIFEST = {
    "name": "test2e_client",
    "version": "14.0.3.0.0",
    "odoo-license": "EE",
    "env-ver": "2",
    "docker-images": [
        "odoo jobiols/odoo-jeo:14.0",
        "postgres postgres:13",
    ],
    "git-repos": ["https://github.com/jobiols/odoo-enterprise.git"],
}


class TestRepository(OdooEnvTestCase):
    def setUp(self):
        super().setUp()
        self.mock_config_data.return_value["clients"] = [
            {"test_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
            {"test2_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
            {"test2e_client": "/home/jobiols/tmp/odoo-env/odoo_env/data"},
        ]

    def test_install(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir (index 1 in new structure)
        psql_dir = f"{OeConfig().base_dir}odoo-14.0/test_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_install2(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST2_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test2_client")
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir
        psql_dir = f"{OeConfig().base_dir}odoo-14.0/test2_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_install2_enterprise(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST2E_CLIENT_MANIFEST
        options = MockArgs(
            debug=True,
            extract_sources=False,
            client="test2e_client",
        )
        oe = OdooEnv(options)
        cmds = oe.install()

        # Base dir mkdir
        self.assertEqual(cmds[0].command, ["mkdir", "-p", OeConfig().base_dir])

        # Postgresql dir mkdir
        psql_dir = f"{OeConfig().base_dir}odoo-14.0e/test2e_client/postgresql"
        self.assertEqual(cmds[1].command, ["mkdir", "-p", psql_dir])

    def test_cmd(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
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
            f"{OeConfig().base_dir}odoo-14.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "WDB_SOCKET_SERVER=wdb",
            "-e",
            "WDB_NO_BROWSER_AUTO_OPEN=True",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:14.0",
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
        options = MockArgs(debug=False, client="test_client")
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
            f"{OeConfig().base_dir}odoo-14.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "aeroo:aeroo",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:14.0",
            "--logfile=/var/log/odoo/odoo.log",
            "-d",
            "test_client_prod",
        ]
        self.assertEqual(cmds[0].command, command)

    def test_pull_images(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        self.assertEqual(cmds[0].command, ["docker", "pull", "jobiols/odoo-jeo:14.0"])

    def test_update(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
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
            f"{OeConfig().base_dir}odoo-14.0/test_client/config:/opt/odoo/etc/:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/data_dir:/opt/odoo/data:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/log:/var/log/odoo:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/sources:/opt/odoo/custom-addons:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/backup_dir:/var/odoo/backups/:rw",
            "-e",
            "ODOO_CONF=/dev/null",
            "--link",
            "pg-test_client:db",
            "jobiols/odoo-jeo:14.0",
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
        options = MockArgs(debug=False, client="test_client")
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
            f"{OeConfig().base_dir}odoo-14.0/test_client/backup_dir/:/backup:rw",
            "-v",
            f"{OeConfig().base_dir}odoo-14.0/test_client/data_dir/filestore:/filestore:rw",
            "-e",
            "NEW_DBNAME=test_client_prod",
            "-e",
            "ZIPFILE=bkp.zip",
            "-e",
            "DEACTIVATE=True",
            "--link",
            "pg-test_client:db",
            DBTOOLS_IMAGE,
        ]
        self.assertEqual(cmds[0].command, command)

    def test_download_image_sources(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(
            debug=True,
            extract_sources=True,
            client="test_client",
        )
        oe = OdooEnv(options)
        cmds = oe.pull_images()

        extract_src_cmd = next(
            (c for c in cmds if c._usr_msg and "Extracting src" in c._usr_msg),
            None,
        )
        self.assertIsNotNone(
            extract_src_cmd,
            "Expected 'Extracting src' command in pull_images() debug mode",
        )
        assert extract_src_cmd is not None
        base = OeConfig().base_dir
        expected_src = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{base}odoo-14.0/src:/dest",
            "jobiols/odoo-jeo:14.0.debug",
            "cp",
            "-r",
            "/usr/lib/python3/dist-packages/odoo/.",
            "/dest/",
        ]
        self.assertEqual(extract_src_cmd.command, expected_src)

        extract_lib_cmd = next(
            (c for c in cmds if c._usr_msg and "Extracting lib" in c._usr_msg),
            None,
        )
        self.assertIsNotNone(
            extract_lib_cmd,
            "Expected 'Extracting lib' command in pull_images() debug mode",
        )
        assert extract_lib_cmd is not None
        expected_lib = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{base}odoo-14.0/lib:/dest",
            "jobiols/odoo-jeo:14.0.debug",
            "cp",
            "-r",
            "/usr/local/lib/python3.9/dist-packages/.",
            "/dest/",
        ]
        self.assertEqual(extract_lib_cmd.command, expected_lib)

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
        repo = GitRepo("https://github.com/jobiols/project.git", "14.0")
        self.assertEqual(
            repo.clone,
            "clone --depth 1  -b 14.0 https://github.com/jobiols/project.git",
        )

    def test_repo2_clone(self):
        repo = GitRepo("https://github.com/jobiols/project.git", "14.0")
        self.assertEqual(repo.dir_name, "project")

    def test_ensure_network_skips_when_exists(self):
        """SC-03: check_args() returns False when docker network inspect exits 0."""

        mock_parent = MagicMock()
        mock_parent.verbose = False

        cmd = EnsureNetworkCommand(
            mock_parent,
            command=["docker", "network", "create", "odoo-net"],
            usr_msg="Starting odoo-net network if needed",
            args="odoo-net",
        )

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch(
            "odoo_env.command.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = cmd.check_args()

        self.assertFalse(result)
        mock_run.assert_called_once_with(
            ["docker", "network", "inspect", "odoo-net"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def test_ensure_network_runs_when_absent(self):
        """SC-04: check_args() returns True when docker network inspect exits non-zero."""

        mock_parent = MagicMock()
        mock_parent.verbose = False

        cmd = EnsureNetworkCommand(
            mock_parent,
            command=["docker", "network", "create", "odoo-net"],
            usr_msg="Starting odoo-net network if needed",
            args="odoo-net",
        )

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch(
            "odoo_env.command.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = cmd.check_args()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["docker", "network", "inspect", "odoo-net"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def test_server_help(self):
        """oe -H genera docker run --rm con entrypoint odoo y --help."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.server_help()

        expected = [
            "docker",
            "run",
            "--rm",
            "--name",
            "help",
            "--entrypoint",
            "odoo",
            "jobiols/odoo-jeo:14.0",
            "--help",
        ]
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0].command, expected)

    def test_run_environment_prod(self):
        """oe -R modo prod: EnsureNetwork + postgres (sin ports) + aeroo."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.run_environment()

        psql_dir = f"{OeConfig().base_dir}odoo-14.0/test_client/postgresql/"

        self.assertEqual(cmds[0].command, ["docker", "network", "create", "odoo-net"])

        expected_postgres = [
            "docker",
            "run",
            "-d",
            "--name",
            "pg-test_client",
            "--network",
            "odoo-net",
            "--restart",
            "unless-stopped",
            "-v",
            f"{psql_dir}:/var/lib/postgresql/data:rw",
            "-e",
            "POSTGRES_USER=odoo",
            "-e",
            "POSTGRES_PASSWORD=odoo",
            "postgres:13",
        ]
        self.assertEqual(cmds[1].command, expected_postgres)

        expected_aeroo = [
            "docker",
            "run",
            "-d",
            "--name",
            "aeroo",
            "--restart",
            "always",
            "jobiols/aeroo-docs",
        ]
        self.assertEqual(cmds[2].command, expected_aeroo)
        self.assertEqual(len(cmds), 3)

    def test_run_environment_debug(self):
        """oe -R modo debug: EnsureNetwork + postgres (con port 5432) + aeroo + wdb."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.run_environment()

        psql_dir = f"{OeConfig().base_dir}odoo-14.0/test_client/postgresql/"

        self.assertEqual(cmds[0].command, ["docker", "network", "create", "odoo-net"])

        expected_postgres = [
            "docker",
            "run",
            "-d",
            "--name",
            "pg-test_client",
            "--network",
            "odoo-net",
            "--restart",
            "unless-stopped",
            "-p",
            "5432:5432",
            "-v",
            f"{psql_dir}:/var/lib/postgresql/data:rw",
            "-e",
            "POSTGRES_USER=odoo",
            "-e",
            "POSTGRES_PASSWORD=odoo",
            "postgres:13",
        ]
        self.assertEqual(cmds[1].command, expected_postgres)

        expected_aeroo = [
            "docker",
            "run",
            "-d",
            "--name",
            "aeroo",
            "--restart",
            "always",
            "jobiols/aeroo-docs",
        ]
        self.assertEqual(cmds[2].command, expected_aeroo)

        expected_wdb = [
            "docker",
            "run",
            "-d",
            "--name",
            "wdb",
            "--network",
            "odoo-net",
            "--restart",
            "unless-stopped",
            "-p",
            "1984:1984",
            WDB_IMAGE_DEFAULT,
        ]
        self.assertEqual(cmds[3].command, expected_wdb)
        self.assertEqual(len(cmds), 4)

    def test_verbose_flag_true(self):
        """OdooEnv.verbose returns True when -v is passed."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", verbose=True)
        oe = OdooEnv(options)
        self.assertTrue(oe.verbose)

    def test_verbose_flag_false(self):
        """OdooEnv.verbose returns False when -v is not passed."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", verbose=False)
        oe = OdooEnv(options)
        self.assertFalse(oe.verbose)

    def test_verbose_prints_command(self):
        """Command.subprocess_call calls msg.run when verbose=True."""
        mock_parent = MagicMock()
        mock_parent.verbose = True

        cmd = Command(mock_parent, command=["echo", "hello"])

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("odoo_env.command.subprocess.run", return_value=mock_result):
            with patch("odoo_env.command.msg") as mock_msg:
                cmd.subprocess_call(["echo", "hello"])

        self.assertTrue(mock_msg.run.called)

    def test_stop_environment_prod(self):
        """oe -S modo prod: stop+rm para pg-xxx y aeroo, sin wdb."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.stop_environment()

        commands = [c.command for c in cmds]
        self.assertIn(["docker", "stop", "pg-test_client"], commands)
        self.assertIn(["docker", "rm", "pg-test_client"], commands)
        self.assertIn(["docker", "stop", "aeroo"], commands)
        self.assertIn(["docker", "rm", "aeroo"], commands)
        # stop debe ir antes que rm para cada contenedor
        self.assertLess(
            commands.index(["docker", "stop", "pg-test_client"]),
            commands.index(["docker", "rm", "pg-test_client"]),
        )
        self.assertLess(
            commands.index(["docker", "stop", "aeroo"]),
            commands.index(["docker", "rm", "aeroo"]),
        )
        # sin wdb en prod
        self.assertNotIn(["docker", "stop", "wdb"], commands)
        self.assertNotIn(["docker", "rm", "wdb"], commands)

    def test_restore_links_postgres_container(self):
        """oe --restore incluye --link pg-test_client:db para que dbtools resuelva 'db'."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", restore=True)
        oe = OdooEnv(options)
        cmds = oe.build_commands()

        restore_cmd = next(
            (c for c in cmds if DBTOOLS_IMAGE in c.command),
            None,
        )
        self.assertIsNotNone(restore_cmd, "No se generó comando de restore")
        assert restore_cmd is not None
        cmd = restore_cmd.command
        self.assertIn("--link", cmd)
        link_index = cmd.index("--link")
        self.assertEqual(cmd[link_index + 1], "pg-test_client:db")

    def test_restore_uses_client_name_not_database(self):
        """oe --restore no confunde client_name con database.

        El bug era que build_commands pasaba 'database' como primer arg a
        restore(), pero la firma espera 'client_name' primero.
        """
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", restore=True)
        oe = OdooEnv(options)
        cmds = oe.build_commands()

        restore_cmd = next(
            (c for c in cmds if DBTOOLS_IMAGE in c.command),
            None,
        )
        self.assertIsNotNone(restore_cmd, "No se generó comando de restore")
        assert restore_cmd is not None
        # El volumen de backup debe contener test_client, no test_client_prod
        backup_volume = next(
            (part for part in restore_cmd.command if "backup_dir" in part),
            None,
        )
        self.assertIsNotNone(backup_volume)
        assert backup_volume is not None
        self.assertIn("test_client", backup_volume)
        self.assertNotIn("test_client_prod", backup_volume)

    def test_qa_passes_full_module_name(self):
        """oe -Q modulo_a_testear genera -u modulo_a_testear, no -u m.

        El bug era modules_to_test[0] que rebanaba el string al primer carácter.
        """
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(
            debug=False, client="test_client", modules_to_test="modulo_a_testear"
        )
        oe = OdooEnv(options)
        cmds = oe.build_commands()

        all_commands = [c.command for c in cmds]
        run_cmd = next(
            (
                c
                for c in all_commands
                if "--test-enable" in c or "--stop-after-init" in c
            ),
            None,
        )
        self.assertIsNotNone(run_cmd, "No se generó comando de test")
        assert run_cmd is not None
        u_index = run_cmd.index("-u")
        self.assertEqual(run_cmd[u_index + 1], "modulo_a_testear")

    def test_base_dir_does_not_require_client(self):
        """oe --base-dir /x no falla si no hay cliente configurado."""
        self.mock_config_data.return_value["client"] = None
        options = MockArgs(base_dir="/nuevo/dir/")
        conf = OeConfig(options)
        conf.persist_config()
        self.assertEqual(OeConfig().base_dir, "/nuevo/dir/")

    def test_base_dir_saved_as_string(self):
        """--base-dir /mi/dir guarda un string, no una lista."""
        options = MockArgs(base_dir="/mi/dir/")
        conf = OeConfig(options)
        conf.persist_config()
        self.assertIsInstance(OeConfig().base_dir, str)
        self.assertEqual(OeConfig().base_dir, "/mi/dir/")

    def test_stop_environment_debug(self):
        """oe -S modo debug: stop+rm para pg-xxx, aeroo y wdb."""
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.stop_environment()

        commands = [c.command for c in cmds]
        self.assertIn(["docker", "stop", "pg-test_client"], commands)
        self.assertIn(["docker", "rm", "pg-test_client"], commands)
        self.assertIn(["docker", "stop", "wdb"], commands)
        self.assertIn(["docker", "rm", "wdb"], commands)
        # stop wdb debe ir antes que rm wdb
        self.assertLess(
            commands.index(["docker", "stop", "wdb"]),
            commands.index(["docker", "rm", "wdb"]),
        )


class TestGetPacks(OdooEnvTestCase):

    def _make_oe_with_version(self, version: int):

        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            type(oe._client),
            "numeric_ver",
            new_callable=PropertyMock,
            return_value=float(version),
        ):
            result = oe.get_packs()
        return result

    def test_get_packs_v14_returns_src_lib(self):
        result = self._make_oe_with_version(14)
        self.assertEqual(result, ["src", "lib"])

    def test_get_packs_v18_returns_src_lib(self):
        result = self._make_oe_with_version(18)
        self.assertEqual(result, ["src", "lib"])

    def test_get_packs_v14_not_dist_packages(self):
        result = self._make_oe_with_version(14)
        self.assertNotEqual(result, ["dist-packages", "dist-local-packages"])


class TestCreateTestDb(OdooEnvTestCase):
    """Tests for the create-test-db feature."""

    # ------- 2.1 discover_modules_in_cwd() tests (RED: method doesn't exist yet) -------

    def _make_mock_entry(self, name, is_dir, has_manifest):
        """Create a mock Path entry for iterdir."""
        entry = MagicMock(spec=Path)
        entry.name = name
        entry.is_dir.return_value = is_dir
        manifest_mock = MagicMock()
        manifest_mock.is_file.return_value = has_manifest
        entry.__truediv__.return_value = manifest_mock
        return entry

    def test_discover_modules_finds_manifest_dirs(self):
        entries = [
            self._make_mock_entry("module_a", True, True),
            self._make_mock_entry("module_b", True, True),
            self._make_mock_entry("not_a_module", True, False),
            self._make_mock_entry("some_file.txt", False, False),
        ]
        with patch("os.getcwd", return_value="/fake/cwd"):
            with patch("pathlib.Path.iterdir", return_value=entries):
                result = EnvironmentManager.discover_modules_in_cwd()
        self.assertEqual(result, ["module_a", "module_b"])

    def test_discover_modules_empty_cwd(self):
        with patch("os.getcwd", return_value="/fake/cwd"):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = EnvironmentManager.discover_modules_in_cwd()
        self.assertEqual(result, [])

    def test_discover_modules_ignores_hidden_dirs(self):
        entries = [
            self._make_mock_entry(".git", True, False),
        ]
        with patch("os.getcwd", return_value="/fake/cwd"):
            with patch("pathlib.Path.iterdir", return_value=entries):
                result = EnvironmentManager.discover_modules_in_cwd()
        self.assertNotIn(".git", result)

    def test_discover_modules_ignores_root_manifest(self):
        entries = [
            self._make_mock_entry("__manifest__.py", False, False),
        ]
        with patch("os.getcwd", return_value="/fake/cwd"):
            with patch("pathlib.Path.iterdir", return_value=entries):
                result = EnvironmentManager.discover_modules_in_cwd()
        self.assertEqual(result, [])

    def test_discover_modules_does_not_recurse(self):
        entries = [
            self._make_mock_entry("module_c", True, True),
        ]
        with patch("os.getcwd", return_value="/fake/cwd"):
            with patch("pathlib.Path.iterdir", return_value=entries):
                result = EnvironmentManager.discover_modules_in_cwd()
        self.assertEqual(result, ["module_c"])

    # ------- 2.2 _build_module_command install test (RED: method doesn't exist) -------

    def test_build_module_command_install(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        env_mgr = EnvironmentManager(oe)
        result = env_mgr._build_module_command(
            "dimec_test", ["module_a", "module_b"], "-i"
        )
        self.assertEqual(len(result), 1)
        cmd = result[0]
        self.assertIn("-i", cmd.command)
        self.assertIn("module_a, module_b", cmd.command)
        self.assertIn("-d", cmd.command)
        self.assertIn("dimec_test", cmd.command)
        self.assertIn("--stop-after-init", cmd.command)
        self.assertIn("--logfile=false", cmd.command)
        self.assertNotIn("--test-enable", cmd.command)
        self.assertTrue(cmd.usr_msg.startswith("Installing "))
        self.assertIn("dimec_test", cmd.usr_msg)

    # ------- 2.3 update() regression test (PASS: baseline before refactor) -------

    def test_update_still_works_after_refactor(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        result = oe.update("test_client_prod", ["all"])
        self.assertEqual(len(result), 1)
        cmd = result[0]
        self.assertIn("-u", cmd.command)
        self.assertIn("all", cmd.command)
        self.assertIn("-d", cmd.command)
        self.assertIn("test_client_prod", cmd.command)
        self.assertIn("--stop-after-init", cmd.command)
        self.assertTrue(cmd.usr_msg.startswith("Performing update of "))

    # ------- 4.1 zero-modules guard (RED: create_test_db doesn't exist) -------

    def test_create_test_db_zero_modules_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=[]
        ):
            with patch.object(
                OdooEnv, "_db_exists", return_value=False
            ) as mock_db_exists:
                with self.assertRaises(OeError) as ctx:
                    oe.create_test_db()
                self.assertIn("No module", str(ctx.exception))
                mock_db_exists.assert_not_called()

    # ------- 4.2 confirm-yes proceeds (RED) -------

    def test_create_test_db_confirm_yes_proceeds(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch("sys.stdin.isatty", return_value=True):
                    with patch("builtins.input", return_value="y"):
                        with patch.object(Path, "is_file", return_value=True):
                            result = oe.create_test_db()
        self.assertGreater(len(result), 0)

    # ------- 4.3 confirm-no aborts (RED) -------

    def test_create_test_db_confirm_no_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch("sys.stdin.isatty", return_value=True):
                    with patch("builtins.input", return_value="n"):
                        with self.assertRaises(OeError) as ctx:
                            oe.create_test_db()
                        self.assertIn("Aborted", str(ctx.exception))

    # ------- 4.4 non-interactive aborts (RED) -------

    def test_create_test_db_non_interactive_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch("sys.stdin.isatty", return_value=False):
                    with self.assertRaises(OeError) as ctx:
                        oe.create_test_db()
                    self.assertIn("not a terminal", str(ctx.exception))

    # ------- 4.5 EOFError aborts (RED) -------

    def test_create_test_db_eof_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch("sys.stdin.isatty", return_value=True):
                    with patch("builtins.input", side_effect=EOFError):
                        with self.assertRaises(OeError) as ctx:
                            oe.create_test_db()
                        self.assertIn("input stream ended", str(ctx.exception))

    # ------- 4.6 full command composition (RED) -------

    def test_create_test_db_command_composition(self):

        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        backup_dir = "/odoo_ar/odoo-14.0/test_client/backup_dir/"
        with patch.object(
            EnvironmentManager,
            "discover_modules_in_cwd",
            return_value=["module_a", "module_b"],
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(
                    type(oe._client),
                    "backup_dir",
                    new_callable=PropertyMock,
                    return_value=backup_dir,
                ):
                    with patch.object(Path, "is_file", return_value=True):
                        result = oe.create_test_db()

        self.assertEqual(len(result), 4)

        # Command 0: cp
        self.assertEqual(
            result[0].command,
            ["cp", f"{backup_dir}bkp_test/test.zip", f"{backup_dir}test.zip"],
        )
        self.assertIn("Copying seed", result[0].usr_msg)

        # Command 1: restore
        self.assertIn(DBTOOLS_IMAGE, result[1].command)
        self.assertIn("ZIPFILE=test.zip", result[1].command)
        self.assertIn("NEW_DBNAME=test_client_test", result[1].command)
        self.assertNotIn("DEACTIVATE", result[1].command)

        # Command 2: rm
        self.assertEqual(result[2].command, ["rm", f"{backup_dir}test.zip"])
        self.assertIn("Removing temporary", result[2].usr_msg)

        # Command 3: install
        self.assertIn("-i", result[3].command)
        self.assertIn("module_a, module_b", result[3].command)
        self.assertIn("-d", result[3].command)
        self.assertIn("test_client_test", result[3].command)
        self.assertIn("--stop-after-init", result[3].command)
        self.assertNotIn("--test-enable", result[3].command)

    # ------- 4.7 seed-missing aborts (RED) -------

    def test_create_test_db_seed_missing_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in_cwd", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=False):
                    with self.assertRaises(OeError) as ctx:
                        oe.create_test_db()
                    self.assertIn("Seed", str(ctx.exception))

    # ------- 4.8 dispatch from build_commands (RED: old msg.err still fires) -------

    def test_create_test_db_dispatched_from_build_commands(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(oe, "create_test_db", return_value=["fake_cmd"]) as mock_ctdb:
            result = oe.build_commands()
            mock_ctdb.assert_called_once()
            self.assertIn("fake_cmd", result)
