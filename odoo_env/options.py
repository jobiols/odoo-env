# -*- coding: utf-8 -*-

from odoo_env.messages import Msg
from odoo_env.config import OeConfig


def get_client(args):
    if args.client:
        OeConfig().save_client(args.client[0])
        return args.client[0]
    else:
        client = OeConfig().get_client()
        if client:
            return client
        else:
            Msg().err('Need -c option (client name). Process aborted')


def get_database(args):
    if args.database:
        return args.database[0]
    else:
        client = get_client(args)
        if client:
            default_database = client + '_prod'
            Msg().inf('Using default database: %s, use -d to '
                      'specify another database' % default_database)
            return default_database
        else:
            Msg().err('Need -c option (client name). Process aborted')


def get_module(args):
    if args.module:
        return args.module
    else:
        Msg().inf('Updating all modules. Use -m to specify single module '
                  'or a comma separated list of modules.')
        return ['all']


def get_backup_file(args):
    if args.backup_file:
        return args.backup_file[0]
    else:
        Msg().inf('Restoring newest backup. Use -f to store specific one.')
        return False


def get_param(args, param):
    if param == 'client':
        return get_client(args)

    if param == 'database':
        return get_database(args)

    if param == 'module':
        return get_module(args)

    if param == 'backup_file':
        return get_backup_file(args)

    if param == 'deactivate':
        if args.deactivate:
            return args.deactivate
        else:
            return False
