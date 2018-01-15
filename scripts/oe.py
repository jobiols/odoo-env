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

    parser.add_argument(
        '--debug',
        action='store_true',
        help='This option has three efects: '
             '1.- when doing an update database, (option -u) it forces debug '
             'mode. 2.- When running environment (option -R) it opens port '
             '5432 to access postgres server databases. '
             '3.- when doing a pull (option -p) it clones the full repo i.e. '
             'does not issue --depth 1 to git ')

    parser.add_argument('--no-repos',
                        action='store_true',
                        help='Does not clone or pull repos used with -i or -p')

    parser.add_argument('-R', '--run-env',
                        action='store_true',
                        help="Run database and aeroo images.")

    parser.add_argument('-r', '--run-cli',
                        action='store_true',
                        help="Run client odoo, requires -c options")


    args = parser.parse_args()
    options = {}
    options['verbose'] = args.verbose
    options['debug'] = args.debug
    options['no-repos'] = args.no_repos
    options['nginx'] = False

    if args.install_cli:
        client_name = get_param(args, 'client')
        commands = OdooEnv(options).install_client(client_name)

    if args.run_env:
        client_name = get_param(args, 'client')
        commands = OdooEnv(options).run_environment(client_name)

    if args.run_cli:
        client_name = get_param(args, 'client')
        commands = OdooEnv(options).run_client(client_name)


    # ejecutar comandos
    for command in commands:

        if command and command.check():
            Msg().inf(command.usr_msg)
            command.execute()
