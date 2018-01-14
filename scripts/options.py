# -*- coding: utf-8 -*-

from messages import Msg


def get_param(args, param):
    if param == 'client':
        if args.client:
            return args.client[0]
        else:
            Msg().err('Need -c option (client name). Process aborted')
