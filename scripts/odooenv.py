# -*- coding: utf-8 -*-

from messages import Msg
from client import Client
from command import Command
from constants import BASE_DIR


class OdooEnv(object):
    """ Esta clase toma los parametros de parser y con cada metodo, que
        corresponde a una opcion, devuelve una lista de tuplas con accion y
        mensaje. El mensaje puede estar o no.
        Si hay mensaje se muestra antes de ejecutar la accion
    """

    def __init__(self, args):
        self._args = args
        self._client = False

    def install_client(self):
        """ Instalacion de cliente,
            Si es la primera vez crea la estructura de directorios
        """
        msg = 'Installing client {}'.format(self.client.name)
        ret = []

        # create base dir with sudo
        cmd = Command(command='sudo mkdir {}',
                      args=BASE_DIR,
                      chck='path.isdir',
                      usr_msg=msg,
                      env=self)
        ret.append(cmd)

        # create all hierarchy
        for working_dir in ['postgresql', 'config', 'data', 'log', 'sources']:
            cmd = Command(command='mkdir -p {}',
                          args='{}odoo-{}/{}'.format(
                              BASE_DIR,
                              'odoo-',
                              self.client.version,
                              working_dir),
                          chck='path.isdir',
                          env=self)
            ret.append(cmd)

        return ret

    @property
    def client(self):
        if not self._args.client:
            Msg().err('need -c option (client name)')

        self._client = Client(self, self._args.client[0])

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def args(self):
        return self._args