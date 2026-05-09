from unittest.mock import patch, PropertyMock

from odoo_env.odooenv import OdooEnv
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.test_helpers import MockArgs, OdooEnvTestCase


class TestDebugMountings(OdooEnvTestCase):

    def _make_em(self, odoo_version: int):
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        with patch.object(
            type(oe._client), "numeric_ver", new_callable=PropertyMock, return_value=float(odoo_version)
        ), patch.object(
            type(oe._client), "version_dir", new_callable=PropertyMock, return_value=f"/odoo_ar/odoo-{odoo_version}.0/"
        ):
            em = EnvironmentManager(oe)
            em._parent = oe
            result = em._get_debug_mountings()
        return result

    def test_odoo14_lib_mount(self):
        result = self._make_em(14)
        self.assertEqual(
            result["/odoo_ar/odoo-14.0/lib"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo14_src_mount(self):
        result = self._make_em(14)
        self.assertEqual(
            result["/odoo_ar/odoo-14.0/src"],
            {"bind": "/usr/lib/python3/dist-packages/odoo"},
        )

    def test_odoo15_lib_mount(self):
        result = self._make_em(15)
        self.assertEqual(
            result["/odoo_ar/odoo-15.0/lib"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo16_lib_mount(self):
        result = self._make_em(16)
        self.assertEqual(
            result["/odoo_ar/odoo-16.0/lib"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo17_lib_mount(self):
        result = self._make_em(17)
        self.assertEqual(
            result["/odoo_ar/odoo-17.0/lib"],
            {"bind": "/usr/local/lib/python3.10/dist-packages/"},
        )

    def test_odoo18_lib_mount(self):
        result = self._make_em(18)
        self.assertEqual(
            result["/odoo_ar/odoo-18.0/lib"],
            {"bind": "/usr/local/lib/python3.12/dist-packages/"},
        )

    def test_odoo19_unchanged(self):
        result = self._make_em(19)
        self.assertEqual(
            result,
            {
                "/odoo_ar/odoo-19.0/src": {"bind": "/odoo/odoo-src"},
                "/odoo_ar/odoo-19.0/site-packages": {
                    "bind": "/odoo/venv/lib/python3.10/site-packages"
                },
            },
        )

    def test_legacy_11_has_extra_addons(self):
        result = self._make_em(11)
        self.assertIn("/odoo_ar/odoo-11.0/extra-addons", result)

    def test_legacy_12_has_extra_addons(self):
        result = self._make_em(12)
        self.assertIn("/odoo_ar/odoo-12.0/extra-addons", result)

    def test_legacy_13_has_extra_addons(self):
        result = self._make_em(13)
        self.assertIn("/odoo_ar/odoo-13.0/extra-addons", result)

    def test_unknown_version_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._make_em(20)

    def test_odoo14_uses_src_key(self):
        result = self._make_em(14)
        self.assertIn("/odoo_ar/odoo-14.0/src", result)

    def test_odoo14_uses_lib_key(self):
        result = self._make_em(14)
        self.assertIn("/odoo_ar/odoo-14.0/lib", result)

    def test_odoo14_no_dist_packages_key(self):
        result = self._make_em(14)
        self.assertNotIn("/odoo_ar/odoo-14.0/dist-packages", result)

    def test_odoo14_no_dist_local_packages_key(self):
        result = self._make_em(14)
        self.assertNotIn("/odoo_ar/odoo-14.0/dist-local-packages", result)

    def test_odoo17_lib_contains_python310(self):
        result = self._make_em(17)
        lib_bind = result.get("/odoo_ar/odoo-17.0/lib", {}).get("bind", "")
        self.assertIn("python3.10", lib_bind)

    def test_odoo14_src_bind_is_odoo_path(self):
        result = self._make_em(14)
        src_bind = result.get("/odoo_ar/odoo-14.0/src", {}).get("bind", "")
        self.assertEqual(src_bind, "/usr/lib/python3/dist-packages/odoo")

    def test_odoo14_lib_bind_ends_with_slash(self):
        result = self._make_em(14)
        lib_bind = result.get("/odoo_ar/odoo-14.0/lib", {}).get("bind", "")
        self.assertTrue(lib_bind.endswith("/"))


class TestEnvironmentManager(OdooEnvTestCase):

    def test_install_never_calls_extract_sources(self):
        with patch("odoo_env.odooenv.OdooEnv.do_extract_sources") as mock_extract:
            options = MockArgs(debug=True, client="test_client")
            oe = OdooEnv(options)
            oe.install()
            mock_extract.assert_not_called()

    def test_install_does_not_call_extract_sources_in_debug_mode(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            has_rm_rf = "rm" in c.command and "-rf" in c.command
            self.assertFalse(
                has_rm_rf,
                f"Found rm -rf command in install() debug mode: {c.command}",
            )

    def test_install_does_not_call_extract_sources_in_non_debug_mode(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            has_rm_rf = "rm" in c.command and "-rf" in c.command
            self.assertFalse(
                has_rm_rf,
                f"Found rm -rf command in install() non-debug mode: {c.command}",
            )

    def test_install_does_not_reference_dist_dirs(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            cmd_str = " ".join(str(t) for t in c.command)
            self.assertNotIn(
                "dist-packages",
                cmd_str,
                f"install() references dist-packages: {c.command}",
            )
            self.assertNotIn(
                "dist-local-packages",
                cmd_str,
                f"install() references dist-local-packages: {c.command}",
            )
