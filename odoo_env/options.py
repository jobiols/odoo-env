# -*- coding: utf-8 -*-

from odoo_env.messages import Msg


def get_param(args, param):
    if param == 'client':
        if args.client:
            return args.client[0]
        else:
            Msg().err('Need -c option (client name). Process aborted')

    if param == 'database':
        if args.database:
            return args.database[0]
        else:
            database = args.client[0] + '_prod'
            Msg().inf('Using default database: %s, use -d to '
                      'specify database' % database)
            return database

    if param == 'module':
        if args.module:
            return args.module
        else:
            Msg().inf('Updaging all modules. Use -m to specify single module '
                      'or a comma separated list of modules.')
            return ['all']

    if param == 'backup_file':
        if args.backup_file:
            return args.backup_file[0]
        else:
            Msg().inf('Restoring newest backup. Use -f to store specific one.')
            return False

    if param == 'deactivate':
        if args.deactivate:
            return args.deactivate
        else:
            return False
