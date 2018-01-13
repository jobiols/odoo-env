#!/usr/bin/env python
import argparse
from odooenv import OdooEnv
from execute import Execute

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

    if args.install_cli:
        command = OdooEnv(args).install_client()
        Execute(command)
