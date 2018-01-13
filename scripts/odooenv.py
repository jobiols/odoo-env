# -*- coding: utf-8 -*-

from messages import Msg
from client import Client


class Command(object):
    def __init__(self, param, msg, cmd):
        self._param = param
        self._msg = msg
        self._cmd = cmd

    @property
    def msg(self):
        return self._msg

    @property
    def cmd(self):
        return self._cmd

    @property
    def param(self):
        return self._param


class OdooEnv(object):
    """ Esta clase toma los parametros de parser y con cada metodo, que
        corresponde a una opcion, devuelve una lista de tuplas con accion y
        mensaje. El mensaje puede estar o no.
        Si hay mensaje se muestra antes de ejecutar la accion
    """

    def __init__(self, parser):
        self._args = parser.parse_args()
        self._client = False

    @property
    def client(self):
        if not self._args.client:
            Msg().err('need -c option (client name)')

        self._client = Client(self._args.client[0])

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def install_client(self):
        """ Instalacion de cliente,
            Si es la primera vez crea la estructura de directorios
        """
        msg = 'Installing client {}'.format(self.client.name)
        ret = []

        ret.append(Command('mkdir /odoo', msg, 'comando'))
        return ret
