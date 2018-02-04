# -*- coding: utf-8 -*-

from messages import Msg


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
            Msg().err('Need -d option (database name). Process aborted')

    if param == 'module':
        if args.module:
            return args.module
        else:
            Msg().err('Need -m option (module(s) name). Process aborted')

    if param == 'backup_file':
        if args.backup_file:
            return args.backup_file[0]
        else:
            Msg().err('Need -f option (backup file). Process aborted')
