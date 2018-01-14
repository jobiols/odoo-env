#!/usr/bin/env python
import argparse
from odooenv import OdooEnv
from messages import Msg
from options import get_param

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""
==========================================================================
Odoo Environment Manager v0.0.1 - by jeo Software <jorge.obiols@gmail.com>
==========================================================================
""")

    parser.add_argument(
        '-i',
        '--install-cli',
        action='store_true',
        help="Install client, requires -c option. Creates dir structure, Pull "
             "repos and images, and generate odoo config file")

    parser.add_argument(
        '-c',
        action='append',
        dest='client',
        help="Client name.")

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Go verbose mode. Prints every command")

    args = parser.parse_args()
    options = {}
    options['verbose'] = args.verbose

    if args.install_cli:
        # obtener parametros
        client_name = get_param(args, 'client')
        # invocar instancia
        commands = OdooEnv(options).install_client(client_name)

        # ejecutar comandos
        for c in commands:
            print c.command, c.args, c.usr_msg

        for command in commands:
            if command.usr_msg:
                Msg().inf(command.usr_msg)
            if command and command.check():
                command.execute()
