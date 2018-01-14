# -*- coding: utf-8 -*-

from client import Client
from command import Command, MakedirCommand
import pwd
import os
from constants import BASE_DIR


class OdooEnv(object):
    """
    Implementa metodos que corresponden a cada una de las acciones que se
    proveen en la interfase argparse.

        corresponde a una opcion, devuelve una lista de tuplas con accion y
        mensaje. El mensaje puede estar o no.
        Si hay mensaje se muestra antes de ejecutar la accion

    """

    def __init__(self, options):
        self._options = options
        self._client = False

    def install_client(self, client_name):
        """ Instalacion de cliente,
            Si es la primera vez crea la estructura de directorios
        """
        msg = 'Installing client {}'.format(client_name)

        self._client = Client(self, client_name)

        ret = []

        # create base dir with sudo
        cmd = MakedirCommand(self,
                             command='sudo mkdir {}',
                             args=[BASE_DIR],
                             check='path.isdir',
                             usr_msg=msg)
        ret.append(cmd)

        # change ownership of base dir
        username = pwd.getpwuid(os.getuid()).pw_name
        cmd = Command(self, command='sudo chown {}:{} {}',
                      args=[username, username, BASE_DIR])
        ret.append(cmd)

        # create all hierarchy
        for working_dir in ['postgresql', 'config',
                            'data_dir', 'log', 'sources']:
            cmd = MakedirCommand(self, command='mkdir -p {}',
                                 args=['{}{}'.format(
                                     self.client.base_dir,
                                     working_dir)],
                                 check='path.isdir')
            ret.append(cmd)

        return ret

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def options(self):
        return self._options