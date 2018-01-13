# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from messages import Msg


class Execute(object):
    def __init__(self, commands):
        for command in commands:
            if command.msg:
                Msg().inf(command.msg)
