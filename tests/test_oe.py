# -*- coding: utf-8 -*-
import unittest
from scripts.odooenv import OdooEnv


class TestRepository(unittest.TestCase):
    def test_test(self):

        oe = OdooEnv()
        self.assertEqual(oe.install_client(), 'fake')
