import unittest

from odoo_env.constants import ODOO_PYTHON_MAP


class TestOdooPythonMap(unittest.TestCase):

    def test_map_exact_equality(self):
        self.assertEqual(
            ODOO_PYTHON_MAP,
            {14: "3.9", 15: "3.9", 16: "3.9", 17: "3.10", 18: "3.12"},
        )

    def test_legacy_and_future_keys_absent(self):
        for key in (11, 12, 13, 19):
            self.assertNotIn(key, ODOO_PYTHON_MAP)
