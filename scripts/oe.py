#!/usr/bin/env python
import argparse
from odooenv import OdooEnv
from messages import Msg
from options import get_param

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""
==========================================================================
Odoo Environment Manager v0.1.0 - by jeo Software <jorge.obiols@gmail.com>
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
        help='This option has the following efects: '
             '1.- when doing an update all, (option -u) it forces debug '
             'mode. '
             '2.- When running environment (option -R) it opens port '
             '5432 to access postgres server databases. '
             '3.- when doing a pull (option -p) it clones the full repo i.e. '
             'does not issue --depth 1 to git ')

    parser.add_argument(
        '--no-repos',
        action='store_true',
        help='Does not clone or pull repos used with -i or -p')

    parser.add_argument(
        '-R', '--run-env',
        action='store_true',
        help="Run postgres and aeroo images.")

    parser.add_argument(
        '-r', '--run-cli',
        action='store_true',
        help="Run client odoo, requires -c options")

    parser.add_argument(
        '--no-dbfilter',
        action='store_true',
        help='Eliminates dbfilter: The client can see any database. '
             'Without this, the client can only see databases starting with clientname_')

    parser.add_argument(
        '-S', '--stop-env',
        action='store_true',
        help="Stop postgres and aeroo images.")

    parser.add_argument(
        '-s', '--stop-cli',
        action='store_true',
        help="Stop client images, requires -c options.")

    parser.add_argument(
        '-u', '--update-all',
        action='store_true',
        help="Update all requires -d -c and -m options. "
             "Use --debug to force update with host sources")

    parser.add_argument(
        '-d',
        action='store',
        nargs=1,
        dest='database',
        help="Database name. Note that there is a dbfilter option by default "
             "the database name must begin with clientname_")

    parser.add_argument(
        '-m',
        action='append',
        dest='module',
        help="Module to update or all for updating all the registered "
             "modules. You can specify multiple -m options. i.e. -m all for"
             "all modules -m sales stock for updating sales and stock modules")

    parser.add_argument(
        '--nginx',
        action='store_true',
        help='Add nginx to installation: With -i creates nginx dir w/ sample '
             'config file. with -r starts an nginx container linked to odoo'
             'with -s stops nginx containcer. You must add certificates and '
             'review nginx.conf file.')

    args = parser.parse_args()
    options = {
        'verbose': args.verbose,
        'debug': args.debug,
        'no-repos': args.no_repos,
        'nginx': args.nginx,
        'postfix': False,
        'no-dbfilter': args.no_dbfilter
    }
    commands = []

    if args.install_cli:
        client_name = get_param(args, 'client')
        commands += OdooEnv(options).install_client(client_name)

    if args.stop_env:
        client_name = get_param(args, 'client')
        commands += OdooEnv(options).stop_environment(client_name)

    if args.run_env:
        client_name = get_param(args, 'client')
        commands += OdooEnv(options).run_environment(client_name)

    if args.stop_cli:
        client_name = get_param(args, 'client')
        commands += OdooEnv(options).stop_client(client_name)

    if args.run_cli:
        client_name = get_param(args, 'client')
        commands += OdooEnv(options).run_client(client_name)

    if args.update_all:
        client_name = get_param(args, 'client')
        database = get_param(args, 'database')
        modules = get_param(args, 'module')
        commands += OdooEnv(options).update_all(client_name, database, modules)

    # #####################################################################
    # ejecutar comandos
    # ######################################################################
    for command in commands:
        if command and command.check():
            Msg().inf(command.usr_msg)
            command.execute()
