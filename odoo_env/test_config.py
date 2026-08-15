"""Tests for OeConfig organization resolution.

Covers REQ-INSTALL-009 (organization configuration: --org flag, config key,
default quilsoft-org with persist-on-missing).
"""

import unittest
from unittest.mock import patch

from odoo_env.config import OeConfig
from odoo_env.messages import OeError
from odoo_env.test_helpers import MockArgs, OeConfigPatchTestCase


class TestOrganizationConfig(OeConfigPatchTestCase):
    """Unit tests for OeConfig.get_organization() / save_organization()."""

    # --- REQ-INSTALL-009: default + persist on missing ---

    def test_org_default_when_missing_persists(self):
        conf = self._start({"clients": []})

        org = conf.get_organization()

        self.assertEqual(org, "quilsoft-org")
        self.assertEqual(conf.config_data.get("organization"), "quilsoft-org")
        self.mock_save_config.assert_called()

    # --- REQ-INSTALL-009: read from config, no re-persist ---

    def test_org_read_from_config(self):
        conf = self._start({"clients": [], "organization": "acme-org"})

        org = conf.get_organization()

        self.assertEqual(org, "acme-org")
        self.mock_save_config.assert_not_called()

    # --- REQ-INSTALL-009: save_organization persists ---

    def test_save_organization_persists(self):
        conf = self._start({"clients": []})

        conf.save_organization("acme-org")

        self.assertEqual(conf.config_data.get("organization"), "acme-org")
        self.mock_save_config.assert_called()

    def test_save_organization_noop_when_unchanged(self):
        conf = self._start({"clients": [], "organization": "acme-org"})

        conf.save_organization("acme-org")

        self.mock_save_config.assert_not_called()

    # --- REQ-INSTALL-009: persist_config saves --org flag ---

    def test_persist_config_saves_org_flag(self):
        self.mock_config_data.return_value = {"clients": []}
        conf = OeConfig(MockArgs(debug=False, org="acme-org"))

        conf.persist_config()

        self.assertEqual(conf.config_data.get("organization"), "acme-org")
        self.mock_save_config.assert_called()


class TestPersistClientConfig(OeConfigPatchTestCase):
    """Unit tests for OeConfig.persist_config() with the -c flag (issue #123)."""

    def test_persist_config_saves_client_flag(self):
        """`oe -c <client>` en instalación fresca debe persistir el cliente
        sin abortar. El bug era que persist_config usaba self.client (que llama
        a get_client() y aborta si todavía no hay default).
        """
        self.mock_config_data.return_value = {"clients": []}
        conf = OeConfig(MockArgs(debug=False, client="sama"))

        conf.persist_config()

        self.assertEqual(conf.config_data.get("client"), "sama")
        self.mock_save_config.assert_called()


class TestGetClientError(OeConfigPatchTestCase):
    """Unit tests for the OeConfig.get_client() error message (issue #123)."""

    def test_error_message_mentions_dash_c_not_client(self):
        """El mensaje debe apuntar al flag real (-c), no a --client."""
        conf = self._start({"clients": []})

        with self.assertRaises(OeError) as ctx:
            conf.get_client()

        self.assertIn("-c", str(ctx.exception))
        self.assertNotIn("--client", str(ctx.exception))


class TestSaveConfigDataErrors(unittest.TestCase):
    """Unit tests for OeConfig._save_config_data() I/O error handling.

    En instalación fresca `~/.config/oe/` no existe, así que save_client ->
    _save_config_data corre os.makedirs/open por primera vez. Un fallo de
    escritura debe surgir como OeError (mensaje claro), no como un traceback
    crudo de OSError.
    """

    def setUp(self):
        OeConfig.reset()
        self.get_patcher = patch.object(
            OeConfig, "_get_config_data", return_value={"clients": []}
        )
        self.get_patcher.start()
        self.conf = OeConfig(MockArgs(debug=False))

    def tearDown(self):
        self.get_patcher.stop()
        OeConfig.reset()

    def test_save_raises_oeerror_when_makedirs_fails(self):
        with (
            patch("odoo_env.config.os.path.exists", return_value=False),
            patch("odoo_env.config.os.makedirs", side_effect=OSError("boom")),
        ):
            with self.assertRaises(OeError):
                self.conf._save_config_data()

    def test_save_raises_oeerror_when_open_fails(self):
        with (
            patch("odoo_env.config.os.path.exists", return_value=True),
            patch("odoo_env.config.open", side_effect=OSError("denied"), create=True),
        ):
            with self.assertRaises(OeError):
                self.conf._save_config_data()


if __name__ == "__main__":
    unittest.main()
