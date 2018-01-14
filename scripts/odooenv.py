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

        ##################################################################
        # Create base dir with sudo
        ##################################################################

        cmd = MakedirCommand(self,
                             command='sudo mkdir {}',
                             args=[BASE_DIR],
                             check='path.isdir',
                             usr_msg=msg)
        ret.append(cmd)

        ##################################################################
        # change ownership of base dir
        ##################################################################

        username = pwd.getpwuid(os.getuid()).pw_name
        cmd = Command(self,
                      command='sudo chown {}:{} {}',
                      args=[username, username, BASE_DIR])
        ret.append(cmd)

        ##################################################################
        # create all hierarchy
        ##################################################################
        for working_dir in ['postgresql', 'config', 'data_dir', 'log',
                            'sources', 'image_repos']:
            cmd = MakedirCommand(self, command='mkdir -p {}',
                                 args=['{}{}'.format(
                                     self.client.base_dir, working_dir)],
                                 check='path.isdir')
            ret.append(cmd)

        ##################################################################
        # create dirs for extracting sources only for debug
        ##################################################################
        if self.debug:
            for working_dir in ['dist_packages', 'dist_local_packages']:
                cmd = MakedirCommand(self, command='mkdir -p {}',
                                     args=['{}{}'.format(
                                         self.client.base_dir, working_dir)],
                                     check='path.isdir')
                ret.append(cmd)

        ##################################################################
        # create dirs for nginx & postfix
        ##################################################################

        for working_dir in ['nginx', 'postfix']:
            cmd = MakedirCommand(self, command='mkdir -p {}',
                                 args=['{}{}'.format(
                                     BASE_DIR, working_dir)],
                                 check='path.isdir')
            ret.append(cmd)

        ##################################################################
        # Extracting sources from image if debug enabled
        ##################################################################
        if self.debug:
            module = 'dist-packages'
            msg = 'Extracting {} from image {}.debug'.format(
                module, self.client.image('odoo'))
            command = 'sudo docker run -it --rm '
            command += '--entrypoint=/extract_{}.sh '.format(module)
            command += '-v {}{}/:/mnt/{} '.format(self.client.base_dir,
                                                  module, module)
            command += '{}.debug '.format(self.client.image('odoo'))

            cmd = MakedirCommand(self, command=command,
                                 args='{}{}'.format(self.client.base_dir,
                                                    module),
                                 check='path.isdir',
                                 usr_msg=msg)
            ret.append(cmd)

        return ret

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def debug(self):
        return self._options['debug']

    @property
    def verbose(self):
        return self._options['verbose']
