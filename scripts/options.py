# -*- coding: utf-8 -*-

from messages import Msg
from odooenv import OdooEnv

oe = OdooEnv()
msg = Msg()


class Options(object):

    def list_data(self):
        # if no -c option get all clients else get -c clients
        msg.inf('testeando')
        return oe.list_data()
