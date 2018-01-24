# -*- coding: utf-8 -*-

from client import Client
from command import Command, MakedirCommand, ExtractSourcesCommand, \
    CloneRepo, PullRepo, CreateNginxTemplate

import pwd
import os
from constants import BASE_DIR, IN_CONFIG, IN_DATA, IN_LOG, IN_CUSTOM_ADDONS, \
    IN_DIST_LOCAL_PACKAGES, IN_DIST_PACKAGES, IN_EXTRA_ADDONS


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

    def _process_repos(self):
        """ Clone or update repos as needed
        """
        ret = []
        # do nothing if no-repos option is true

        if self.no_repos:
            return ret

        for repo in self.client.repos:
            ##############################################################
            # Clone repo if it not exist
            ##############################################################

            cmd = CloneRepo(
                self,
                usr_msg='cloning {}'.format(repo.formatted),
                command='git -C {} {}'.format(self.client.sources_dir,
                                              repo.clone),
                args='{}{}'.format(self.client.sources_dir, repo.dir_name)
            )
            ret.append(cmd)

            ##############################################################
            # Update repo if exist
            ##############################################################

            cmd = PullRepo(
                self,
                usr_msg='pulling {}'.format(repo.formatted),
                command='git -C {}{} {}'.format(self.client.sources_dir,
                                                repo.dir_name,
                                                repo.pull),
                args='{}{}'.format(self.client.sources_dir, repo.dir_name)
            )
            ret.append(cmd)

            ##############################################################
            # Create simbolic link
            ##############################################################

            # cmd = MakedirCommand(
            #    self,
            #    usr_msg='simlinking {}'.format(repo.formatted),
            #    command='ln -s {}{} {}{}'.format(
            #        self.client.sources_com, repo.dir_name,
            #        self.client.sources_dir, repo.dir_name),
            #    args='{}{}'.format(self.client.sources_dir, repo.dir_name)
            # )
            # ret.append(cmd)

        return ret

    def install_client(self, client_name):
        """ Instalacion de cliente,
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
        # create all client hierarchy
        ##################################################################
        for w_dir in ['postgresql', 'config', 'data_dir', 'log', 'sources']:
            r_dir = '{}{}'.format(self.client.base_dir, w_dir)
            cmd = MakedirCommand(
                self,
                command='mkdir -p {}'.format(r_dir),
                args='{}'.format(r_dir)
            )
            ret.append(cmd)

        ##################################################################
        # create dir for common sources
        ##################################################################

        # r_dir = '{}'.format(self.client.sources_com)
        # cmd = MakedirCommand(
        #    self,
        #    command='mkdir -p {}'.format(r_dir),
        #    args='{}'.format(r_dir)
        # )
        # ret.append(cmd)

        ##################################################################
        # create dirs for extracting sources, only for debug
        ##################################################################
        if self.debug:

            # no sacamos dist-local-packages
            for w_dir in ['dist-packages', 'extra-addons']:
                r_dir = '{}{}'.format(self.client.version_dir, w_dir)
                cmd = MakedirCommand(
                    self,
                    command='mkdir -p {}'.format(r_dir),
                    args='{}'.format(r_dir)
                )
                ret.append(cmd)

        ##################################################################
        # change o+w for those dirs
        ##################################################################

        if self.debug:
            # no sacamos dist-local-packages
            for w_dir in ['dist-packages', 'extra-addons']:
                r_dir = '{}{}'.format(self.client.version_dir, w_dir)
                cmd = Command(
                    self,
                    command='chmod o+w {}'.format(r_dir)
                )
                ret.append(cmd)

        ##################################################################
        # change o+w for config, data and log
        ##################################################################

        for w_dir in ['config', 'data_dir', 'log']:
            r_dir = '{}{}'.format(self.client.base_dir, w_dir)
            cmd = Command(
                self,
                command='chmod o+w {}'.format(r_dir)
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for nginx if needed
        ##################################################################

        if self.nginx:
            for w_dir in ['cert', 'conf', 'log']:
                r_dir = '{}{}'.format(BASE_DIR, 'nginx/' + w_dir)
                cmd = MakedirCommand(
                    self,
                    command='mkdir -p {}'.format(r_dir),
                    args='{}'.format(r_dir)
                )
                ret.append(cmd)

        ##################################################################
        # create nginx.conf template if needed. Do not overwrite
        ##################################################################

        if self.nginx:
            r_dir = '{}{}'.format(BASE_DIR, 'nginx/conf/')
            cmd = CreateNginxTemplate(
                self,
                command='{}nginx.conf'.format(r_dir),
                args='{}nginx.conf'.format(r_dir),
                usr_msg='Generating nginx.conf template'
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for postfix
        ##################################################################

        if self.postfix:
            r_dir = '{}{}'.format(BASE_DIR, 'postfix')
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
            # no sacamos dist-local-packages
            for module in ['dist-packages', 'extra-addons']:
                msg = 'Extracting {} from image {}.debug'.format(
                    module, self.client.get_image('odoo').name)
                command = 'sudo docker run -it --rm '
                command += '--entrypoint=/extract_{}.sh '.format(module)
                command += '-v {}{}/:/mnt/{} '.format(self.client.version_dir,
                                                      module, module)
                command += '{}.debug '.format(
                    self.client.get_image('odoo').name)

                cmd = ExtractSourcesCommand(
                    self,
                    command=command,
                    args='{}{}'.format(self.client.version_dir, module),
                    usr_msg=msg,
                )
                ret.append(cmd)

        ##################################################################
        # Clone or update repos as needed
        ##################################################################

        ret += self._process_repos()

        ##################################################################
        # End of job
        ##################################################################

        return ret

    def _add_debug_mountings(self):
        ret = '-v {}extra-addons:{} '.format(
            self.client.version_dir, IN_EXTRA_ADDONS)
        ret += '-v {}dist-packages:{} '.format(
            self.client.version_dir, IN_DIST_PACKAGES)
        # no sacamos dist-local-packages
        # ret += '-v {}dist-local-packages:{} '.format(
        #    self.client.version_dir, IN_DIST_LOCAL_PACKAGES)
        return ret

    def _add_normal_mountings(self):
        ret = '-v {}config:{} '.format(self.client.base_dir, IN_CONFIG)
        ret += '-v {}data_dir:{} '.format(self.client.base_dir, IN_DATA)
        ret += '-v {}log:{} '.format(self.client.base_dir, IN_LOG)
        ret += '-v {}sources:{} '.format(self.client.base_dir,
                                         IN_CUSTOM_ADDONS)
        return ret

        return ret

    def stop_environment(self, client_name):
        self._client = Client(self, client_name)
        ret = []

        img2 = 'postgres-{}'.format(self.client.name)

        for image in ['aeroo', img2]:
            cmd = Command(
                self,
                command='sudo docker rm -f {}'.format(image),
                usr_msg='Stopping image {}'.format(image),
            )
            ret.append(cmd)

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
        command += '--name {}-{} '.format(image.short_name, self.client.name)
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
        image = self.client.get_image('aeroo')

        command = 'sudo docker run -d '
        command += '--name={} '.format(image.short_name)
        command += '--restart=always '
        command += image.name
        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)

        return ret

    def stop_client(self, client_name):
        ret = []

        cmd = Command(
            self,
            command='sudo docker rm -f {}'.format(client_name),
            usr_msg='Stopping image {}'.format(client_name),
        )
        ret.append(cmd)

        return ret

    def run_client(self, client_name):

        self._client = Client(self, client_name)
        ret = []

        msg = 'Starting image for client {} on port {}'.format(
            client_name,
            self.client.port
        )

        if self.debug:
            command = 'sudo docker run --rm -it '
        else:
            command = 'sudo docker run -d '

        # a partir de la 10 no se usa aeroo
        if self.client.numeric_ver < 10:
            command += '--link aeroo:aeroo '

        # open port for wdb
        if self.debug:
            command += '-p 1984:1984 '

        # exponer el puerto solo si no tenemos nginx
        if not self.nginx:
            command += '-p {}:8069 '.format(self.client.port)

        if not self.debug:
            # exponer puerto para longpolling
            command += '-p 8072:8072 '

        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings()

        command += '--link postgres-{}:db '.format(self.client.name)

        if not self.debug:
            command += '--restart=always '

        command += '--name {} '.format(self.client.name)

        # si estamos en modo debug agregarlo al nombre de la imagen
        if self.debug:
            command += '-e SERVER_MODE=test '
            command += '{}.debug '.format(self.client.get_image('odoo').name)
        else:
            command += '-e SERVER_MODE= '
            command += '{} '.format(self.client.get_image('odoo').name)

        if not self.no_dbfilter:
            command += '-- --db-filter={}_.* '.format(self.client.name)

        if not self.debug:
            command += '--logfile=/var/log/odoo/odoo.log '
        else:
            command += '--logfile=/dev/stdout '

        # You should use 2 worker threads + 1 cron thread per available CPU,
        # and 1 CPU per 10 concurent users. Make sure you tune the memory
        # limits and cpu limits in your configuration file.
        if self.debug:
            command += '--workers 0 '
        else:
            command += '--workers 0 '

        command += ' --load=web,web_kanban,server_mode,database_tools '

        # number of workers dedicated to cron jobs. Defaults to 2. The workers
        # are threads in multithreading mode and processes in multiprocessing
        # mode.
        command += '--max-cron-threads 1 '

        # Number of requests a worker will process before being recycled and
        # restarted. Defaults to 8196
        command += '--limit-request 8196 '

        # Maximum allowed virtual memory per worker. If the limit is exceeded,
        # the worker is killed and recycled at the end of the current request.
        # Defaults to 640MB
        command += '--limit-memory-soft 2147483648 '

        # Hard limit on virtual memory, any worker exceeding the limit will be
        # immediately killed without waiting for the end of the current request
        # processing. Defaults to 768MB.
        command += '--limit-memory-hard 2684354560 '

        # Prevents the worker from using more than CPU seconds for each
        # request. If the limit is exceeded, the worker is killed. Defaults
        # to 60.
        command += '--limit-time-cpu 1600 '

        # Prevents the worker from taking longer than seconds to process a
        # request. If the limit is exceeded, the worker is killed. Defaults to
        # 120. Differs from --limit-time-cpu in that this is a "wall time"
        # limit including e.g. SQL queries.
        command += '--limit-time-real 3200 '

        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)

        ##################################################################
        # Launching nginx proxy if needed
        ##################################################################

        if self.nginx:
            msg = 'Starting nginx reverse proxy'
            image = self.client.get_image('nginx')

            nginx_dir = self.client.nginx_dir
            command = 'sudo docker run -d '
            command += '-v {}conf:/etc/nginx/conf.d:ro '.format(nginx_dir)
            command += '-v {}cert:/etc/letsencrypt/live/certificadositio '.format(
                nginx_dir)
            command += '-v {}log:/var/log/nginx/ '.format(nginx_dir)
            command += '-p 80:80 '
            command += '-p 443:443 '
            command += '--name={} '.format(image.short_name)
            command += '--link {}:odoo '.format(client_name)
            command += '--restart=always '

            command += image.name
            cmd = Command(
                self,
                command=command,
                usr_msg=msg,
            )
            ret.append(cmd)

        return ret

    def update_all(self, client_name, database, modules):
        self._client = Client(self, client_name)
        ret = []

        command = 'sudo docker run --rm -it '
        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings()
        command += '--link postgres-{}:db '.format(self.client.name)
        command += '{} -- '.format(self.client.get_image('odoo').name)
        command += '--stop-after-init '
        command += '--logfile=false '
        command += '-d {} '.format(database)
        command += '-u {} '.format(', '.join(modules))

        cmd = Command(
            self,
            command=command,
            usr_msg='Performing update all on database {}'.format(database)
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

    @property
    def nginx(self):
        return self._options['nginx']

    @property
    def no_dbfilter(self):
        return self._options['no-dbfilter']

    @property
    def nginx(self):
        return self._options['nginx']

    @property
    def postfix(self):
        return self._options['postfix']
