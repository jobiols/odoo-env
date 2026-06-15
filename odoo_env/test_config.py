"""Tests for OeConfig organization resolution.

Covers REQ-INSTALL-009 (organization configuration: --org flag, config key,
default quilsoft-org with persist-on-missing).
"""

import unittest

from odoo_env.config import OeConfig
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


if __name__ == "__main__":
    unittest.main()
