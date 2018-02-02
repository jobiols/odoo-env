# -*- coding: utf-8 -*-

import unittest
from odooenv import OdooEnv
from command import Command, MakedirCommand, CreateNginxTemplate
from client import Client


class TestRepository(unittest.TestCase):
    def test_01(self):
        options = {
            'debug': False,
            'no-repos': False,
            'nginx': False,
            'postfix': False
        }

        base_dir = '/odoo_ar/'
        oe = OdooEnv(options)
        cmds = oe.install('test_client')
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

    def test_qa(self):
        options = {
            'debug': False
        }
        client_name = 'test_client'
        database = 'cliente_test'
        modules = 'modulo_a_testear'
        repo = 'odoo-addons'
        test_file = 'test_01.py'

        oe = OdooEnv(options)
        client = Client(oe, client_name)

        cmds = oe.qa(client_name, database, modules, repo, test_file,
                     client_test=client)

        cmd = cmds[0]
        self.assertEqual(cmd.usr_msg, 'Performing test test_01.py on repo '
                                      'odoo-addons for client test_client '
                                      'and database cliente_test')

        command = \
            "sudo docker run --rm -it " \
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ " \
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data " \
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo " \
            "-v /odoo_ar/odoo-9.0/test_client/sources:" \
            "/opt/odoo/custom-addons " \
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ " \
            "-p 1984:1984 " \
            "--link postgres-test_client:db jobiols/odoo-jeo:9.0.debug -- " \
            "--stop-after-init " \
            "--logfile=false " \
            "-d cliente_test " \
            "--log-level=test " \
            "--no-xmlrpc " \
            "--test-file=/opt/odoo/custom-addons/odoo-addons/" \
            "modulo_a_testear/tests/test_01.py "

        self.assertEqual(cmd.command, command)

    def test_run_cli(self):
        options = {
            'debug': False,
            'nginx': False,
            'no-dbfilter': False,
        }
        client_name = 'test_client'
        database = 'cliente_test'
        modules = 'modulo_a_testear'
        repo = 'odoo-addons'
        test_file = 'test_01.py'

        oe = OdooEnv(options)
        client = Client(oe, client_name)

        cmds = oe.run_client(client_name)

        cmd = cmds[0]
        self.assertEqual(cmd.usr_msg, 'Starting image for client test_client '
                                      'on port 8069')

        command = \
            "sudo docker run -d " \
            "--link aeroo:aeroo " \
            "-p 8069:8069 " \
            "-p 8072:8072 " \
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ " \
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data " \
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo " \
            "-v /odoo_ar/odoo-9.0/test_client/sources:/opt/odoo/custom-addons " \
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ " \
            "--link postgres-test_client:db " \
            "--restart=always " \
            "--name test_client " \
            "-e ODOO_CONF=/dev/null " \
            "-e SERVER_MODE= " \
            "jobiols/odoo-jeo:9.0 -- " \
            "--db-filter=test_client_.* " \
            "--logfile=/var/log/odoo/odoo.log "

        self.assertEqual(cmd.command, command)
