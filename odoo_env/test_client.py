"""Tests for Client.get_manifest() and get_manifest_from_url() manifest resolution.

Covers REQ-INSTALL-001 through REQ-INSTALL-007 (install-from-url change).
"""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from odoo_env.client import ODOO_ENV_KEYS, Client
from odoo_env.config import OeConfig
from odoo_env.messages import OeError
from odoo_env.test_helpers import MockArgs

BASE_MANIFEST = {
    "name": "test_client",
    "version": "14.0.1.0.0",
    "docker-images": [],
    "git-repos": [],
    "env-ver": "2",
}


class TestGetManifest(unittest.TestCase):
    """Unit tests for Client.get_manifest() and Client.get_manifest_from_url()."""

    def setUp(self):
        OeConfig.reset()

        # Mock OeConfig config data FIRST so singleton init uses mocked data
        self.config_data_patcher = patch.object(OeConfig, "_get_config_data")
        self.mock_config_data = self.config_data_patcher.start()
        self.mock_config_data.return_value = {
            "clients": [],
            "client": "test_client",
            "environment": "prod",
            "base_dir": "/odoo_ar/",
        }

        self.save_config_patcher = patch.object(OeConfig, "_save_config_data")
        self.mock_save_config = self.save_config_patcher.start()

        # Initialize OeConfig singleton so OeConfig() calls inside
        # get_manifest() don't fail with "missing required argument: args"
        OeConfig(MockArgs(debug=False))

        # Mock OeConfig instance methods
        self.get_client_path_patcher = patch.object(OeConfig, "get_client_path")
        self.mock_get_client_path = self.get_client_path_patcher.start()

        self.save_client_path_patcher = patch.object(OeConfig, "save_client_path")
        self.mock_save_client_path = self.save_client_path_patcher.start()

        # Mock subprocess.run to avoid real git operations
        self.subprocess_patcher = patch("odoo_env.client.subprocess.run")
        self.mock_subprocess_run = self.subprocess_patcher.start()

        # Mock get_manifest_from_struct to control manifest discovery
        # (used by get_manifest() — the local/path resolution path).
        self.struct_patcher = patch.object(Client, "get_manifest_from_struct")
        self.mock_get_manifest_from_struct = self.struct_patcher.start()

        # Mock _discover_manifest_from_path to control discovery from a cloned
        # repo (used by get_manifest_from_url() after the bcf2c8b refactor).
        self.discover_patcher = patch.object(Client, "_discover_manifest_from_path")
        self.mock_discover_manifest_from_path = self.discover_patcher.start()

        # Mock check_common and check_v2 to avoid manifest validation in __init__
        self.check_common_patcher = patch.object(Client, "check_common")
        self.mock_check_common = self.check_common_patcher.start()

        self.check_v2_patcher = patch.object(Client, "check_v2")
        self.mock_check_v2 = self.check_v2_patcher.start()

    def tearDown(self):
        self.get_client_path_patcher.stop()
        self.save_client_path_patcher.stop()
        self.config_data_patcher.stop()
        self.save_config_patcher.stop()
        self.subprocess_patcher.stop()
        self.struct_patcher.stop()
        self.discover_patcher.stop()
        self.check_common_patcher.stop()
        self.check_v2_patcher.stop()
        OeConfig.reset()

    # ---------- helper ----------
    def _make_client(self, install, name="test_client"):
        """Create a Client instance bypassing __init__ to avoid side effects."""
        client = Client.__new__(Client)
        client._name = name
        client._args = MockArgs(install=install, debug=False)
        return client

    # ==================================================================
    # Phase 2: RED — failing tests (and regression tests)
    # ==================================================================

    # --- Task 2.1: REQ-INSTALL-001 — Boolean/None guard ---

    def test_install_bool_skips_url(self):
        """install=True (bool) MUST NOT trigger get_manifest_from_url."""
        self.mock_get_client_path.return_value = None
        self.mock_get_manifest_from_struct.return_value = (
            BASE_MANIFEST,
            "/some/path",
        )

        client = self._make_client(install=True)
        manifest = client.get_manifest()

        self.mock_subprocess_run.assert_not_called()
        self.assertIsNotNone(manifest)

    def test_install_none_skips_url(self):
        """install=None MUST NOT trigger get_manifest_from_url."""
        self.mock_get_client_path.return_value = None
        self.mock_get_manifest_from_struct.return_value = (
            BASE_MANIFEST,
            "/some/path",
        )

        client = self._make_client(install=None)
        manifest = client.get_manifest()

        self.mock_subprocess_run.assert_not_called()
        self.assertIsNotNone(manifest)

    # --- Task 2.2: REQ-INSTALL-005/007 — Existing client_path guard ---

    def test_existing_client_path_skips_url_bool(self):
        """Existing client_path MUST skip URL resolution when install=True."""
        self.mock_get_client_path.return_value = Path("/some/existing/path")
        self.mock_get_manifest_from_struct.return_value = (
            BASE_MANIFEST,
            "/some/existing/path",
        )

        client = self._make_client(install=True)
        manifest = client.get_manifest()

        self.mock_subprocess_run.assert_not_called()
        self.assertTrue(self.mock_get_manifest_from_struct.called)
        self.assertIsNotNone(manifest)

    def test_existing_client_path_skips_url_str(self):
        """Existing client_path MUST skip URL resolution even with a string URL."""
        self.mock_get_client_path.return_value = Path("/some/existing/path")
        self.mock_get_manifest_from_struct.return_value = (
            BASE_MANIFEST,
            "/some/existing/path",
        )

        client = self._make_client(install="git@github.com:org/repo.git")
        manifest = client.get_manifest()

        self.mock_subprocess_run.assert_not_called()
        self.assertTrue(self.mock_get_manifest_from_struct.called)
        self.assertIsNotNone(manifest)

    # --- Task 2.3: REQ-INSTALL-003 — URL validation ---

    def test_invalid_url_raises_oe_error(self):
        """Non-git URL MUST raise OeError."""
        self.mock_get_client_path.return_value = None

        client = self._make_client(install="not-a-url")
        with self.assertRaises(OeError) as ctx:
            client.get_manifest_from_url()

        self.assertIn("Invalid git URL", str(ctx.exception))
        self.assertIn("not-a-url", str(ctx.exception))

    def test_empty_url_raises_oe_error(self):
        """Empty string URL MUST raise OeError."""
        self.mock_get_client_path.return_value = None

        client = self._make_client(install="")
        with self.assertRaises(OeError) as ctx:
            client.get_manifest_from_url()

        self.assertIn("Invalid git URL", str(ctx.exception))

    # --- Task 2.4: REQ-INSTALL-002/004 — URL success + save_client_path ---

    def test_url_success_saves_client_path(self):
        """Successful URL clone MUST call save_client_path with the manifest dir."""
        self.mock_get_client_path.return_value = None
        self.mock_discover_manifest_from_path.return_value = (
            BASE_MANIFEST,
            "/tmp/tmpXXX/repo-name",
        )

        client = self._make_client(install="https://github.com/org/repo.git")
        manifest = client.get_manifest_from_url()

        self.mock_subprocess_run.assert_called_once()
        call_args = self.mock_subprocess_run.call_args[0][0]
        self.assertEqual(call_args[0], "git")
        self.assertEqual(call_args[1], "clone")
        self.assertEqual(call_args[2], "--depth")
        self.assertEqual(call_args[3], "1")
        self.assertEqual(call_args[4], "https://github.com/org/repo.git")
        self.mock_save_client_path.assert_called_once_with(
            "test_client", "/tmp/tmpXXX/repo-name"
        )
        self.assertIsNotNone(manifest)

    def test_url_no_manifest_returns_none(self):
        """Clone with no manifest MUST return None and NOT save client_path."""
        self.mock_get_client_path.return_value = None
        self.mock_discover_manifest_from_path.return_value = (None, None)

        client = self._make_client(install="git@github.com:org/repo.git")
        manifest = client.get_manifest_from_url()

        self.assertIsNone(manifest)
        self.mock_save_client_path.assert_not_called()

    def test_url_str_calls_get_manifest_from_url(self):
        """String install with no client_path MUST forward to get_manifest_from_url."""
        self.mock_get_client_path.return_value = None
        self.mock_discover_manifest_from_path.return_value = (
            BASE_MANIFEST,
            "/tmp/path",
        )

        client = self._make_client(install="git@github.com:org/repo.git")
        manifest = client.get_manifest()

        self.mock_subprocess_run.assert_called()
        self.assertIsNotNone(manifest)

    # --- Task 2.5: Clone failure propagation ---

    def test_url_clone_failure_propagates(self):
        """Git clone failure MUST propagate and NOT call save_client_path."""
        self.mock_get_client_path.return_value = None
        self.mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            128, ["git", "clone"]
        )

        client = self._make_client(install="git@github.com:org/repo.git")
        with self.assertRaises(subprocess.CalledProcessError):
            client.get_manifest_from_url()

        self.mock_save_client_path.assert_not_called()


class TestClientDebugFollowsPersistedEnvironment(unittest.TestCase):
    """client.debug debe seguir el environment PERSISTIDO (oe_config.yaml),
    no el flag transitorio --debug de la invocacion actual.

    --debug solo PERSISTE environment=debug; una vez seteado, `oe -w` (sin
    --debug) debe seguir corriendo en debug (workers=0, etc.).
    """

    def setUp(self):
        OeConfig.reset()
        self.config_data_patcher = patch.object(OeConfig, "_get_config_data")
        self.mock_config_data = self.config_data_patcher.start()
        self.save_config_patcher = patch.object(OeConfig, "_save_config_data")
        self.mock_save_config = self.save_config_patcher.start()

    def tearDown(self):
        self.config_data_patcher.stop()
        self.save_config_patcher.stop()
        OeConfig.reset()

    def _client_with_persisted_env(self, environment):
        self.mock_config_data.return_value = {
            "clients": [],
            "client": "test_client",
            "environment": environment,
            "base_dir": "/odoo_ar/",
        }
        # invocacion SIN --debug (p.ej. `oe -w`)
        OeConfig(MockArgs(debug=False))
        client = Client.__new__(Client)
        client._name = "test_client"
        client._args = MockArgs(debug=False)
        return client

    def test_debug_true_when_persisted_environment_is_debug(self):
        client = self._client_with_persisted_env("debug")
        self.assertTrue(
            client.debug,
            "client.debug debe ser True si environment persistido == debug, "
            "aunque la invocacion no traiga --debug",
        )

    def test_debug_false_when_persisted_environment_is_prod(self):
        client = self._client_with_persisted_env("prod")
        self.assertFalse(client.debug)


class TestValidateManifestKeys(unittest.TestCase):
    """Tests for Client.validate_manifest_keys() — typo guard on manifest keys."""

    def test_valid_manifest_passes(self):
        manifest = {
            "name": "test_client",
            "version": "14.0.1.0.0",
            "depends": ["sale"],
            "data": [],
            "config": ["workers = 5"],
            "config-local": ["workers = 0"],
            "git-repos": [],
            "docker-images": [],
            "odoo-license": "CE",
            "env-ver": "2",
            "port": "8069",
        }
        # No debe lanzar
        Client.validate_manifest_keys(manifest, "test_client")

    def test_typo_underscore_instead_of_hyphen_raises_with_suggestion(self):
        manifest = {"name": "c", "config_local": ["workers = 0"]}
        with self.assertRaises(OeError) as ctx:
            Client.validate_manifest_keys(manifest, "c")
        self.assertIn("config_local", str(ctx.exception))
        self.assertIn("config-local", str(ctx.exception))

    def test_typo_git_repos_underscore_raises_with_suggestion(self):
        manifest = {"name": "c", "git_repos": []}
        with self.assertRaises(OeError) as ctx:
            Client.validate_manifest_keys(manifest, "c")
        self.assertIn("git-repos", str(ctx.exception))

    def test_unknown_key_raises_not_recognized(self):
        manifest = {"name": "c", "totally_made_up_xyz": 1}
        with self.assertRaises(OeError) as ctx:
            Client.validate_manifest_keys(manifest, "c")
        self.assertIn("totally_made_up_xyz", str(ctx.exception))
        self.assertIn("not a recognized", str(ctx.exception))

    def test_standard_odoo_keys_pass(self):
        manifest = {
            "name": "c",
            "summary": "x",
            "author": "y",
            "category": "Tools",
            "installable": True,
            "application": False,
            "auto_install": False,
            "external_dependencies": {},
        }
        Client.validate_manifest_keys(manifest, "c")

    def test_full_real_world_manifest_passes(self):
        """Manifiesto real completo (las 10 claves oe + claves Odoo) NO debe fallar."""
        manifest = {
            # claves estandar de Odoo
            "name": "dimec",
            "version": "17.0.1.0.0",
            "category": "Tools",
            "summary": "Customizacion dimec",
            "author": "jeo Software",
            "website": "https://github.com/jobiols/odoo-env",
            "license": "AGPL-3",
            "depends": ["sale_management", "account"],
            "installable": True,
            "application": False,
            # las 10 claves especificas de oe
            "env-ver": "2",
            "odoo-license": "EE",
            "port": "8069",
            "longpolling_port": "8072",
            "prod_server": "ubuntu@my-server",
            "config": ["admin_passwd = secret", "proxy_mode = True", "workers = 2"],
            "config-local": ["admin_passwd = admin", "workers = 0"],
            "git-repos": [
                "git@github.com:quilsoft-org/cl-dimec.git",
                "git@github.com:quilsoft-org/dimec.git -b main",
                "https://github.com/ingadhoc/odoo-argentina.git sub_l10n-ar/odoo-argentina",
            ],
            "docker-images": [
                "odoo jobiols/odoo-ent:17.0e",
                "postgres postgres:14.13-alpine",
            ],
            "external_dependencies": {"python": ["requests", "openpyxl"]},
        }
        # No debe lanzar
        Client.validate_manifest_keys(manifest, "dimec")

    def test_all_odoo_env_keys_are_accepted(self):
        """Cada una de las 10 claves oe debe ser aceptada individualmente."""
        for key in ODOO_ENV_KEYS:
            with self.subTest(key=key):
                Client.validate_manifest_keys({"name": "c", key: "x"}, "c")
