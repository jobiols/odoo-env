#!/usr/bin/env python
import argparse

from options import Options

options = Options()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""
        ==============================================================================
        Docker Odoo Environment Manager v0.0.1 by jeo Software jorge.obiols@gmail.com
        ==============================================================================
    """)

    parser.add_argument('-l', '--list',
                        action='store_true',
                        help="List all data in this server. Clients and images. with "
                             "--issues REPO list the github issues from repo")

    args = parser.parse_args()

    if args.list:
        print options.list_data()
