"""Tests for the `oe --restore` backup-availability guard.

Ensures `oe --restore` fails with a clear message when there is nothing
to restore (missing/empty backup_dir or a named backup file that is absent),
instead of letting the dbtools container crash internally.
"""

import tempfile
from pathlib import Path
from unittest.mock import PropertyMock, patch

from odoo_env.messages import OeError
from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import TEST_CLIENT_MANIFEST, MockArgs, OdooEnvTestCase


class TestRestoreBackupGuard(OdooEnvTestCase):
    """Guard for `oe --restore`: fail clearly when there is nothing to restore."""

    def _make_oe(self):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(debug=False, client="test_client")
        return OdooEnv(options)

    def _patch_backup_dir(self, oe, path):
        return patch.object(
            type(oe.client),
            "backup_dir",
            new_callable=PropertyMock,
            return_value=str(path) + "/",
        )

    def test_missing_backup_dir_raises(self):
        oe = self._make_oe()
        with self._patch_backup_dir(oe, "/nonexistent/path/xyz"):
            with self.assertRaises(OeError) as ctx:
                oe._check_backup_available(backup_file=False)
        self.assertIn("Backup directory does not exist", str(ctx.exception))

    def test_empty_backup_dir_raises(self):
        oe = self._make_oe()
        with tempfile.TemporaryDirectory() as tmp:
            with self._patch_backup_dir(oe, tmp):
                with self.assertRaises(OeError) as ctx:
                    oe._check_backup_available(backup_file=False)
        self.assertIn("No backup files", str(ctx.exception))

    def test_newest_restore_passes_when_zip_present(self):
        oe = self._make_oe()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "backup_2025_01_15.zip").touch()
            with self._patch_backup_dir(oe, tmp):
                # No debe lanzar
                oe._check_backup_available(backup_file=False)

    def test_specific_backup_file_missing_raises_with_available(self):
        oe = self._make_oe()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "other.zip").touch()
            with self._patch_backup_dir(oe, tmp):
                with self.assertRaises(OeError) as ctx:
                    oe._check_backup_available(backup_file="missing.zip")
        text = str(ctx.exception)
        self.assertIn("Backup file not found", text)
        self.assertIn("other.zip", text)

    def test_specific_backup_file_present_passes(self):
        oe = self._make_oe()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "good.zip").touch()
            with self._patch_backup_dir(oe, tmp):
                # No debe lanzar
                oe._check_backup_available(backup_file="good.zip")
