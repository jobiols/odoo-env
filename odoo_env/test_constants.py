import unittest

from odoo_env import constants
from odoo_env.constants import (
    ODOO_V14_DEBUG_MOUNTS,
    ODOO_VERSION_MAP,
    OdooVersionInfo,
)


class TestOdooVersionMap(unittest.TestCase):

    def test_odoo_version_info_is_namedtuple(self):
        info = OdooVersionInfo("3.9", "/a", "/b")
        self.assertEqual(info.python, "3.9")
        self.assertEqual(info.src, "/a")
        self.assertEqual(info.lib, "/b")

    def test_version14_not_in_version_map(self):
        # v14 usa el layout .deb viejo (dist-packages entero), definido en
        # ODOO_V14_DEBUG_MOUNTS, no en ODOO_VERSION_MAP (src/lib).
        self.assertNotIn(14, ODOO_VERSION_MAP)

    def test_v14_debug_mounts_whole_dist_packages(self):
        self.assertEqual(
            ODOO_V14_DEBUG_MOUNTS["dist-packages"],
            "/usr/lib/python3/dist-packages",
        )

    def test_v14_debug_mounts_dist_local_packages(self):
        self.assertEqual(
            ODOO_V14_DEBUG_MOUNTS["dist-local-packages"],
            "/usr/local/lib/python3.9/dist-packages/",
        )

    def test_v14_debug_mounts_has_no_src_lib(self):
        self.assertNotIn("src", ODOO_V14_DEBUG_MOUNTS)
        self.assertNotIn("lib", ODOO_V14_DEBUG_MOUNTS)

    def test_version15_layout(self):
        self.assertEqual(ODOO_VERSION_MAP[15].python, "3.9")
        self.assertEqual(
            ODOO_VERSION_MAP[15].src, "/usr/lib/python3/dist-packages/odoo"
        )
        self.assertEqual(
            ODOO_VERSION_MAP[15].lib, "/usr/local/lib/python3.9/dist-packages"
        )

    def test_version16_same_as_14(self):
        self.assertEqual(ODOO_VERSION_MAP[16].python, "3.9")
        self.assertEqual(
            ODOO_VERSION_MAP[16].src, "/usr/lib/python3/dist-packages/odoo"
        )
        self.assertEqual(
            ODOO_VERSION_MAP[16].lib, "/usr/local/lib/python3.9/dist-packages"
        )

    def test_version17_python310(self):
        self.assertEqual(ODOO_VERSION_MAP[17].python, "3.10")
        self.assertEqual(
            ODOO_VERSION_MAP[17].lib, "/usr/local/lib/python3.10/dist-packages"
        )

    def test_version18_python312(self):
        self.assertEqual(ODOO_VERSION_MAP[18].python, "3.12")
        self.assertEqual(
            ODOO_VERSION_MAP[18].lib, "/usr/local/lib/python3.12/dist-packages"
        )

    def test_legacy_and_future_keys_absent(self):
        for key in (11, 12, 13, 14, 19):
            self.assertNotIn(key, ODOO_VERSION_MAP)

    def test_odoo_python_map_absent(self):
        self.assertFalse(
            hasattr(constants, "ODOO_PYTHON_MAP"),
            "ODOO_PYTHON_MAP must not exist in constants",
        )
