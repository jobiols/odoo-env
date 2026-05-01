from unittest.mock import patch

from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import MockArgs, OdooEnvTestCase


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
