from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

from odoo_env.constants import DBTOOLS_IMAGE
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.messages import OeError
from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import TEST_CLIENT_MANIFEST, MockArgs, OdooEnvTestCase


class TestQaCli(OdooEnvTestCase):
    """Tests del dispatch CLI de qa (oe -Q / -Q all)."""

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

    @patch("odoo_env.odooenv.TestRunner.discover_test_modules")
    def test_qa_all_expands_to_discovered_testable_modules(self, mock_discover):
        """oe -Q all genera -u con la lista de módulos que tienen tests/."""
        mock_discover.return_value = ["mod_a", "mod_b"]
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", modules_to_test="all")
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
        self.assertEqual(run_cmd[u_index + 1], "mod_a,mod_b")

    @patch("odoo_env.odooenv.TestRunner.discover_test_modules")
    def test_qa_all_aborts_when_no_testable_modules(self, mock_discover):
        """oe -Q all sin módulos con tests/ debe abortar, no correr con -u vacío."""
        mock_discover.return_value = []
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client", modules_to_test="all")
        oe = OdooEnv(options)
        with self.assertRaises(OeError):
            oe.build_commands()


class TestCreateTestDb(OdooEnvTestCase):
    """Tests for the create-test-db feature."""

    # ------- 2.1 discover_modules_in() tests -------

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
        with patch("pathlib.Path.iterdir", return_value=entries):
            result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertEqual(result, ["module_a", "module_b"])

    def test_discover_modules_empty_dir(self):
        with patch("pathlib.Path.iterdir", return_value=[]):
            result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertEqual(result, [])

    def test_discover_modules_ignores_hidden_dirs(self):
        entries = [
            self._make_mock_entry(".git", True, False),
        ]
        with patch("pathlib.Path.iterdir", return_value=entries):
            result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertNotIn(".git", result)

    def test_discover_modules_ignores_root_manifest(self):
        entries = [
            self._make_mock_entry("__manifest__.py", False, False),
        ]
        with patch("pathlib.Path.iterdir", return_value=entries):
            result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertEqual(result, [])

    def test_discover_modules_does_not_recurse(self):
        entries = [
            self._make_mock_entry("module_c", True, True),
        ]
        with patch("pathlib.Path.iterdir", return_value=entries):
            result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertEqual(result, ["module_c"])

    def test_discover_modules_does_not_use_process_cwd(self):
        """Regresión: no debe depender de os.getcwd().

        Antes del fix, discover_modules_in_cwd() escaneaba el CWD real del
        proceso, así que `oe --create-test-db` solo funcionaba bien parado
        justo en sources_dir. Ahora recibe el directorio explícito y nunca
        consulta os.getcwd().
        """
        entries = [self._make_mock_entry("module_a", True, True)]
        with patch(
            "os.getcwd", side_effect=AssertionError("must not call os.getcwd()")
        ):
            with patch("pathlib.Path.iterdir", return_value=entries):
                result = EnvironmentManager.discover_modules_in("/fake/sources")
        self.assertEqual(result, ["module_a"])

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
        # Odoo -i needs comma WITHOUT space
        self.assertIn("module_a,module_b", cmd.command)
        self.assertNotIn("module_a, module_b", cmd.command)
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
        with patch.object(EnvironmentManager, "discover_modules_in", return_value=[]):
            with patch.object(
                OdooEnv, "_db_exists", return_value=False
            ) as mock_db_exists:
                with self.assertRaises(OeError) as ctx:
                    oe.create_test_db()
                self.assertIn("No module", str(ctx.exception))
                mock_db_exists.assert_not_called()

    def test_create_test_db_discovers_from_custom_modules_dir(self):
        """Regresión: los módulos custom viven en sources/<cliente>/, no en
        sources/ a secas.

        Bajo sources_dir/ cuelgan varios repos (cl-<cliente>, <cliente>,
        y posibles dependencias como odoo-addons/). Los módulos
        customizados a testear/instalar viven específicamente en
        sources_dir/<cliente>/, así que create_test_db debe descubrir
        módulos ahí, no en sources_dir directo (que solo tiene carpetas de
        repos como hijos inmediatos, no módulos).
        """
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ) as mock_discover:
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=True):
                    oe.create_test_db()

        mock_discover.assert_called_once_with(oe.client.custom_modules_dir)

    # ------- 4.2 confirm-yes proceeds (RED) -------

    def test_create_test_db_confirm_yes_proceeds(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
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
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(Path, "is_file", return_value=True):
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
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(Path, "is_file", return_value=True):
                    with patch("sys.stdin.isatty", return_value=False):
                        with self.assertRaises(OeError) as ctx:
                            oe.create_test_db()
                        self.assertIn("not a terminal", str(ctx.exception))

    # ------- 4.5 EOFError aborts (RED) -------

    def test_create_test_db_eof_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(Path, "is_file", return_value=True):
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
            "discover_modules_in",
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
        self.assertIn("module_a,module_b", result[3].command)
        self.assertNotIn("module_a, module_b", result[3].command)
        self.assertIn("-d", result[3].command)
        self.assertIn("test_client_test", result[3].command)
        self.assertIn("--stop-after-init", result[3].command)
        self.assertNotIn("--test-enable", result[3].command)

    # ------- 4.7 seed-missing aborts (RED) -------

    def test_create_test_db_seed_missing_aborts(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=False):
                    with self.assertRaises(OeError) as ctx:
                        oe.create_test_db()
                    self.assertIn("Seed", str(ctx.exception))

    def test_create_test_db_seed_guard_runs_before_db_confirm_prompt(self):
        """El seed guard corre antes del prompt interactivo de la DB.

        Si el seed falta, debe abortar con el error de seed sin llegar a
        preguntarle nada al usuario sobre la DB existente (aunque
        _db_exists() sea True). Antes del fix, el prompt corría primero:
        el usuario contestaba y recién ahí se enteraba de que el seed
        faltaba.
        """
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(Path, "is_file", return_value=False):
                    with patch("builtins.input") as mock_input:
                        with self.assertRaises(OeError) as ctx:
                            oe.create_test_db()
                        self.assertIn("Seed", str(ctx.exception))
                        mock_input.assert_not_called()

    # ------- 4.9 staging-collision guard: never silently clobbers an
    # existing backup that happens to be named test.zip; prompts instead -------

    def test_create_test_db_staging_collision_confirm_yes_proceeds(self):
        """Si el usuario confirma, sí puede pisar el test.zip existente."""
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=True):
                    with patch.object(Path, "exists", return_value=True):
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="y"):
                                result = oe.create_test_db()
        self.assertGreater(len(result), 0)

    def test_create_test_db_staging_collision_confirm_no_aborts(self):
        """Si el usuario NO confirma, aborta sin tocar el archivo existente."""
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=True):
                    with patch.object(Path, "exists", return_value=True):
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="n"):
                                with self.assertRaises(OeError) as ctx:
                                    oe.create_test_db()
                                self.assertIn("Aborted", str(ctx.exception))

    def test_create_test_db_staging_collision_non_interactive_aborts(self):
        """Sin terminal interactiva no se puede confirmar: aborta, no pisa."""
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            EnvironmentManager, "discover_modules_in", return_value=["module_a"]
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with patch.object(Path, "is_file", return_value=True):
                    with patch.object(Path, "exists", return_value=True):
                        with patch("sys.stdin.isatty", return_value=False):
                            with self.assertRaises(OeError) as ctx:
                                oe.create_test_db()
                            self.assertIn("not a terminal", str(ctx.exception))

    # ------- 4.8 dispatch from build_commands (RED: old msg.err still fires) -------

    def test_create_test_db_dispatched_from_build_commands(self):
        options = MockArgs(create_test_db=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(oe, "create_test_db", return_value=["fake_cmd"]) as mock_ctdb:
            result = oe.build_commands()
            mock_ctdb.assert_called_once()
            self.assertIn("fake_cmd", result)

    # ------- 4.10 _db_exists uses safe psql parameterization, not f-string -------

    def test_db_exists_does_not_interpolate_database_name_into_sql(self):
        """El nombre de DB no debe ir embebido literal dentro del texto SQL.

        Antes del fix: f"...datname='{database}'" interpolaba el valor
        directo en la query — un patrón frágil (rompe, o peor, con una
        comilla en el nombre). Ahora se pasa como variable psql (-v) y se
        referencia con :'var', que psql cita de forma segura.
        """
        options = MockArgs(client="test_client")
        oe = OdooEnv(options)
        fake_result = MagicMock(returncode=0, stdout="1\n")
        with patch("subprocess.run", return_value=fake_result) as mock_run:
            oe._db_exists("weird'name")

        cmd = mock_run.call_args[0][0]
        sql_arg = cmd[-1]
        self.assertNotIn("weird'name", sql_arg)
        self.assertIn("-v", cmd)
        v_index = cmd.index("-v")
        self.assertEqual(cmd[v_index + 1], "dbname=weird'name")
        self.assertIn(":'dbname'", sql_arg)

    def test_db_exists_true_when_query_returns_1(self):
        options = MockArgs(client="test_client")
        oe = OdooEnv(options)
        fake_result = MagicMock(returncode=0, stdout="1\n")
        with patch("subprocess.run", return_value=fake_result):
            self.assertTrue(oe._db_exists("test_client_test"))

    def test_db_exists_false_when_query_returns_empty(self):
        options = MockArgs(client="test_client")
        oe = OdooEnv(options)
        fake_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=fake_result):
            self.assertFalse(oe._db_exists("test_client_test"))
