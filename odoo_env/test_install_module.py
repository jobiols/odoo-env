"""Unit tests for `oe -I` (install a module into the client database).

Strict TDD. Run:
    PYTHONPATH=. venv/bin/python -m unittest odoo_env.test_install_module
"""

import unittest
from unittest.mock import PropertyMock, patch

from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.messages import OeError
from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import MockArgs, OdooEnvTestCase, docker_run_base, module_map


def _make_oe(modules, **kwargs):
    options = MockArgs(
        debug=False, client="test_client", install_module=modules, **kwargs
    )
    return OdooEnv(options)


class TestInstallModuleGuards(OdooEnvTestCase):
    """-I must fail fast when the module is not on disk or the DB is missing."""

    def test_unknown_module_raises(self):
        oe = _make_oe("nope")
        with patch.object(
            EnvironmentManager,
            "discover_all_modules",
            return_value=module_map("sale"),
        ):
            with self.assertRaises(OeError):
                oe.install_module("nope", "test_client_prod")

    def test_missing_db_raises(self):
        oe = _make_oe("sale")
        with patch.object(
            EnvironmentManager,
            "discover_all_modules",
            return_value=module_map("sale"),
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=False):
                with self.assertRaises(OeError):
                    oe.install_module("sale", "test_client_prod")


class TestInstallModulePartition(OdooEnvTestCase):
    """-I partitions requested modules into install (-i) vs update (-u)."""

    def _call(self, modules, installed):
        oe = _make_oe(modules)
        with patch.object(
            EnvironmentManager,
            "discover_all_modules",
            return_value=module_map("sale", "stock"),
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(
                    OdooEnv, "_installed_modules", return_value=set(installed)
                ):
                    with patch.object(EnvironmentManager, "install_module") as mock_em:
                        oe.install_module(modules, "test_client_prod")
        return mock_em

    def test_new_module_installs(self):
        mock = self._call("sale", installed=[])
        args = mock.call_args[0]
        self.assertEqual(args[0], "test_client_prod")
        self.assertEqual(args[1], ["sale"])  # install_modules
        self.assertEqual(args[2], [])  # update_modules

    def test_installed_module_updates(self):
        mock = self._call("sale", installed=["sale"])
        args = mock.call_args[0]
        self.assertEqual(args[1], [])
        self.assertEqual(args[2], ["sale"])

    def test_mixed_partitions(self):
        mock = self._call("sale,stock", installed=["sale"])
        args = mock.call_args[0]
        self.assertEqual(args[1], ["stock"])
        self.assertEqual(args[2], ["sale"])


class TestInstallModuleCommand(OdooEnvTestCase):
    """EnvironmentManager.install_module builds a single docker run command."""

    def _make_em(self, numeric_ver=14.0):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        patcher = patch.object(
            type(oe._client),
            "numeric_ver",
            new_callable=PropertyMock,
            return_value=float(numeric_ver),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return EnvironmentManager(oe)

    def _build(self, em, install, update):
        with patch("sys.stdin.isatty", return_value=True):
            return em.install_module(
                "test_client_prod", install_modules=install, update_modules=update
            )[0].command

    def test_install_new_module_uses_i(self):
        em = self._make_em()
        cmd = self._build(em, ["sale"], [])
        joined = " ".join(cmd)
        self.assertIn("-i sale", joined)
        self.assertNotIn("-u", joined)
        self.assertIn("--stop-after-init", joined)
        self.assertIn("--logfile=false", joined)

    def test_update_installed_module_uses_u(self):
        em = self._make_em()
        cmd = self._build(em, [], ["sale"])
        joined = " ".join(cmd)
        self.assertIn("-u sale", joined)
        self.assertNotIn("-i ", joined)

    def test_mixed_uses_both_verbs(self):
        em = self._make_em()
        cmd = self._build(em, ["stock"], ["sale"])
        joined = " ".join(cmd)
        self.assertIn("-i stock", joined)
        self.assertIn("-u sale", joined)

    def test_adds_with_demo_for_ge19_install(self):
        em = self._make_em(numeric_ver=19.0)
        cmd = self._build(em, ["sale"], [])
        joined = " ".join(cmd)
        self.assertIn("--with-demo", joined)

    def test_omits_with_demo_for_le18(self):
        em = self._make_em(numeric_ver=17.0)
        cmd = self._build(em, ["sale"], [])
        joined = " ".join(cmd)
        self.assertNotIn("--with-demo", joined)

    def test_omits_with_demo_when_only_updating(self):
        # --with-demo only matters at initial install, never at update.
        em = self._make_em(numeric_ver=19.0)
        cmd = self._build(em, [], ["sale"])
        joined = " ".join(cmd)
        self.assertNotIn("--with-demo", joined)

    def test_full_command_shape(self):
        em = self._make_em()
        cmd = self._build(em, ["sale"], [])
        expected = docker_run_base() + [
            "--stop-after-init",
            "--logfile=false",
            "-d",
            "test_client_prod",
            "-i",
            "sale",
        ]
        self.assertEqual(cmd, expected)


class TestBuildInstallDatabase(OdooEnvTestCase):
    """oe -I resolves the target database like -u (default prod, -d override)."""

    def _build(self, **kwargs):
        oe = _make_oe("sale", **kwargs)
        with patch.object(
            EnvironmentManager,
            "discover_all_modules",
            return_value=module_map("sale"),
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(OdooEnv, "_installed_modules", return_value=set()):
                    with patch.object(EnvironmentManager, "install_module") as mock_em:
                        oe.build_commands()
        return mock_em

    def test_build_install_defaults_to_prod_db(self):
        mock = self._build()
        self.assertEqual(mock.call_args[0][0], "test_client_prod")

    def test_build_install_honors_d_override(self):
        mock = self._build(database="my_custom_db")
        self.assertEqual(mock.call_args[0][0], "my_custom_db")


if __name__ == "__main__":
    unittest.main()
