# -*- coding: utf-8 -*-

import unittest
from odooenv import OdooEnv
from command import Command, MakedirCommand, CreateNginxTemplate


class TestRepository(unittest.TestCase):
    def test_01(self):
        options = {
            'debug': False,
            'no-repos': False,
            'nginx': False,
            'postfix': False
        }

        base_dir = '/odoo_ar_test/'
        oe = OdooEnv(options)
        cmds = oe.install_client('test_client')
        self.assertEqual(
            cmds[0].args, base_dir)
        self.assertEqual(
            cmds[0].command, 'sudo mkdir ' + base_dir)
        self.assertEqual(
            cmds[0].usr_msg, 'Installing client test_client')

        self.assertEqual(
            cmds[2].args, '{}odoo-9.0/test_client/postgresql'.format(base_dir))
        self.assertEqual(
            cmds[2].command,
            'mkdir -p {}odoo-9.0/test_client/postgresql'.format(base_dir))
        self.assertEqual(
            cmds[2].usr_msg, False)

    def test_02(self):
        options = {
            'debug': False,
            'no-repos': False,
            'nginx': False,
            'postfix': False
        }
        oe = OdooEnv(options)

        # si no tiene argumentos para chequear no requiere chequeo
        c = Command(oe, command='cmd', usr_msg='hola')
        self.assertEqual(c.command, 'cmd')
        self.assertEqual(c.usr_msg, 'hola')
        self.assertEqual(c.args, False)
        self.assertEqual(c.check(), True)

        c = MakedirCommand(oe, command='cmd', args='no_existe_este_directorio')
        self.assertEqual(c.check_args(), True)

        c = CreateNginxTemplate(oe, command='cmd', args='no_exist',
                                usr_msg='Testing msg')
        self.assertEqual(c.usr_msg, 'Testing msg')
