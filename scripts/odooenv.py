# -*- coding: utf-8 -*-

from client import Client
from command import Command, MakedirCommand, ExtractSourcesCommand

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

        self._client = Client(self, client_name)
        ret = []

        ##################################################################
        # Create base dir with sudo
        ##################################################################
        msg = 'Installing client {}'.format(client_name)
        cmd = MakedirCommand(
            self,
            command='sudo mkdir {}'.format(BASE_DIR),
            args=BASE_DIR,
            usr_msg=msg
        )
        ret.append(cmd)

        ##################################################################
        # change ownership of base dir
        ##################################################################

        username = pwd.getpwuid(os.getuid()).pw_name
        cmd = Command(
            self,
            command='sudo chown {}:{} {}'.format(username, username, BASE_DIR)
        )
        ret.append(cmd)

        ##################################################################
        # create all hierarchy
        ##################################################################
        for w_dir in ['postgresql', 'config', 'data_dir', 'log',
                      'sources', 'image_repos']:
            cmd = MakedirCommand(
                self,
                command='mkdir -p {}{}'.format(self.client.base_dir, w_dir)
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for extracting sources only for debug
        ##################################################################
        if self.debug:
            for w_dir in ['dist-packages', 'dist-local-packages']:
                cmd = MakedirCommand(
                    self, command='mkdir -p {}{}'.format(self.client.base_dir,
                                                         w_dir)
                )
                ret.append(cmd)

        ##################################################################
        # change o+w of both dirs
        ##################################################################

        if self.debug:
            for w_dir in ['dist-packages', 'dist-local-packages']:
                cmd = Command(
                    self,
                    command='chmod o+w {}{}'.format(self.client.base_dir,
                                                    w_dir)
                )
                ret.append(cmd)

        ##################################################################
        # create dirs for nginx & postfix
        ##################################################################

        for w_dir in ['nginx', 'postfix']:
            cmd = MakedirCommand(
                self,
                command='mkdir -p {}{}'.format(BASE_DIR, w_dir)
            )
            ret.append(cmd)

        ##################################################################
        # Extracting sources from image if debug enabled
        ##################################################################
        if self.debug:
            for module in ['dist-packages', 'dist-local-packages']:
                msg = 'Extracting {} from image {}.debug'.format(
                    module, self.client.image('odoo'))
                command = 'sudo docker run -it --rm '
                command += '--entrypoint=/extract_{}.sh '.format(module)
                command += '-v {}{}/:/mnt/{} '.format(self.client.base_dir,
                                                      module, module)
                command += '{}.debug '.format(self.client.image('odoo'))

                cmd = ExtractSourcesCommand(
                    self, command=command,
                    args='{}{}'.format(self.client.base_dir, module),
                    usr_msg=msg
                )
                ret.append(cmd)

        ##################################################################
        # End of job
        ##################################################################

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
