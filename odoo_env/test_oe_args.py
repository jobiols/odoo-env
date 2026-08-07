"""argparse-level tests for the oe CLI (--org flag and -i CLIENT metavar).

Covers REQ-INSTALL-009 (organization flag) and the -i metavar change.
"""

import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from odoo_env.oe import parse_args


class TestParseArgs(unittest.TestCase):
    """Tests for parse_args() handling of --org and -i."""

    def test_org_flag_parsed(self):
        with patch.object(sys, "argv", ["oe", "--org", "acme-org"]):
            args = parse_args()
        self.assertEqual(args.org, "acme-org")

    def test_install_name_parsed(self):
        with patch.object(sys, "argv", ["oe", "-i", "labutic"]):
            args = parse_args()
        self.assertEqual(args.install, "labutic")

    def test_help_shows_client_metavar_and_org(self):
        buf = io.StringIO()
        with patch.object(sys, "argv", ["oe", "--help"]):
            with contextlib.redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    parse_args()
        out = buf.getvalue()
        self.assertIn("CLIENT", out)
        self.assertIn("--org", out)
        self.assertNotIn("REPO_URL", out)


if __name__ == "__main__":
    unittest.main()
