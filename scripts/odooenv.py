# -*- coding: utf-8 -*-

from client import Client
from command import Command, MakedirCommand, ExtractSourcesCommand, \
    CloneRepo, PullRepo

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

    def _update_repos(self):
        ret = []
        # do nothing if no-repos option is true

        if self.no_repos:
            return ret

        for repo in self.client.repos:
            ##############################################################
            # Clone repo if not exist
            ##############################################################

            cmd = CloneRepo(
                self,
                usr_msg='clonning {}'.format(repo.formatted),
                command='git -C {} clone {}'.format(self.client.sources_dir,
                                                    repo.url),
                args='{}{}'.format(self.client.sources_dir, repo.dir_name)
            )
            ret.append(cmd)

            ##############################################################
            # Update repo if exist
            ##############################################################

            cmd = PullRepo(
                self,
                usr_msg='pulling {}'.format(repo.formatted),
                command='git -C {}{} pull {}'.format(self.client.sources_dir,
                                                     repo.dir_name,
                                                     repo.url),
                args='{}{}'.format(self.client.sources_dir, repo.dir_name)
            )
            ret.append(cmd)

        return ret

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
            r_dir = '{}{}'.format(self.client.base_dir, w_dir)
            cmd = MakedirCommand(
                self,
                command='mkdir -p {}'.format(r_dir),
                args='{}'.format(r_dir)
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for extracting sources, only for debug
        ##################################################################
        if self.debug:

            for w_dir in ['dist-packages', 'dist-local-packages']:
                r_dir = '{}{}'.format(self.client.base_dir, w_dir)
                cmd = MakedirCommand(
                    self,
                    command='mkdir -p {}'.format(r_dir),
                    args='{}'.format(r_dir)
                )
                ret.append(cmd)

        ##################################################################
        # change o+w of both dirs
        ##################################################################

        if self.debug:
            for w_dir in ['dist-packages', 'dist-local-packages']:
                r_dir = '{}{}'.format(self.client.base_dir, w_dir)
                cmd = Command(
                    self,
                    command='chmod o+w {}'.format(r_dir)
                )
                ret.append(cmd)

        ##################################################################
        # create dirs for nginx & postfix
        ##################################################################

        for w_dir in ['nginx', 'postfix']:
            r_dir = '{}'.format(BASE_DIR, w_dir)
            cmd = MakedirCommand(
                self,
                command='mkdir -p {}'.format(r_dir),
                args='{}'.format(r_dir)
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
                    self,
                    command=command,
                    args='{}{}'.format(self.client.base_dir, module),
                    usr_msg=msg,
                )
                ret.append(cmd)

        ##################################################################
        # Clone or update repos as needed
        ##################################################################

        ret += self._update_repos()

        ##################################################################
        # End of job
        ##################################################################

        return ret

    def run_environment(self, client_name):
        """
        :return: devuelve los comandos en una lista
        """
        self._client = Client(self, client_name)
        ret = []

        ##################################################################
        # Launching postgres Image
        ##################################################################

        image = self.client.get_image('postgres')

        msg = 'Starting postgres image v{}'.format(image.version)
        command = 'sudo docker run -d '
        if self.debug:
            command += '-p 5432:5432 '
        command += '-e POSTGRES_USER=odoo '
        command += '-e POSTGRES_PASSWORD=odoo '
        command += '-v {}:/var/lib/postgresql/data '.format(
            self.client.psql_dir)
        command += '--restart=always '
        command += '--name {} '.format(image.short_name)
        command += image.name

        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)

        ##################################################################
        # Launching aeroo Image if v < 10
        ##################################################################

        msg = 'Starting aeroo image'
        params = 'sudo docker run -d '
        params += '--name={} '.format(image.short_name)
        params += '--restart=always '
        params += image.image
        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)

        return ret

    @property
    def client(self):
        return self._client

    @property
    def debug(self):
        return self._options['debug']

    @property
    def verbose(self):
        return self._options['verbose']

    @property
    def no_repos(self):
        return self._options['no-repos']
