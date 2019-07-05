# -*- coding: utf-8 -*-

try:
    from client import Client
    from command import Command, MakedirCommand, ExtractSourcesCommand, \
        CloneRepo, PullRepo, CreateNginxTemplate, MessageOnly
    from constants import BASE_DIR, IN_CONFIG, IN_DATA, IN_LOG, \
        IN_CUSTOM_ADDONS, IN_DIST_PACKAGES, IN_EXTRA_ADDONS, IN_BACKUP_DIR
except ImportError:
    from odoo_env.client import Client
    from odoo_env.command import Command, MakedirCommand, \
        ExtractSourcesCommand, CloneRepo, PullRepo, CreateNginxTemplate, \
        MessageOnly
    from odoo_env.constants import BASE_DIR, IN_CONFIG, IN_DATA, IN_LOG, \
        IN_CUSTOM_ADDONS, IN_DIST_PACKAGES, IN_EXTRA_ADDONS, IN_BACKUP_DIR
import pwd
import os


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

    def backup_list(self, client_name):
        """ Listar los archivos disponibles para restore
        """
        self._client = Client(self, client_name)
        ret = []

        filenames = []
        # walk the backup dir
        for root, dirs, files in os.walk(self.client.backup_dir):
            for filedesc in files:
                filename, file_extension = os.path.splitext(filedesc)
                if file_extension == '.zip':
                    filenames.append(filedesc)

        if len(filenames):
            filenames.sort()
            msg = 'List of available backups for client {} \n\n'.format(
                client_name)
            for filedesc in filenames:
                msg += filedesc + '\n'
        else:
            msg = 'There are no files to restore'

        cmd = MessageOnly(
            self,
            command=False,
            usr_msg=msg,
        )
        ret.append(cmd)
        return ret

    def restore(self, client_name, database, backup_file):
        """ Restaurar un backup desde el directorio backup_dir
        """

        self._client = Client(self, client_name)
        image = self.client.get_image('postgres')

        ret = []

        msg = 'Restoring database {}'.format(
            database
        )

        command = 'sudo docker run --rm -i '
        command += '--link pg-{}:db '.format(client_name)
        command += '-v {}:/backup '.format(self.client.backup_dir)
        command += '-v {}data_dir/filestore:/filestore '.format(
            self.client.base_dir)
        command += '--env ZIPFILE={} '.format(backup_file)
        command += '--env NEW_DBNAME={} '.format(database)
        command += 'jobiols/restore '

        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)
        return ret

    def write_config(self, client_name):
        """ Escribe el config file
        """
        self._client = Client(self, client_name)
        ret = []

        ret += self.run_client(client_name, write_config=True)

        return ret

    def install(self, client_name):
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
        for w_dir in ['postgresql', 'config', 'data_dir', 'backup_dir', 'log',
                      'sources']:
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
        # change o+w for config, data, log and backup_dir
        ##################################################################

        for w_dir in ['config', 'data_dir', 'log', 'backup_dir']:
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
                usr_msg='Generating nginx.conf template',
                client_name=client_name
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for postfix
        ##################################################################

        #if self.postfix:
        #    r_dir = '{}{}'.format(BASE_DIR, 'postfix')
        #    cmd = MakedirCommand(
        #        self,
        #        command='mkdir -p {}'.format(r_dir),
        #        args='{}'.format(r_dir)
        #    )
        #    ret.append(cmd)

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

        return ret

    def _add_debug_mountings(self, version):

        if version >= 11:
            idp = IN_DIST_PACKAGES.format('3')
        else:
            idp = IN_DIST_PACKAGES.format('2.7')

        ret = '-v {}extra-addons:{} '.format(
            self.client.version_dir, IN_EXTRA_ADDONS)
        ret += '-v {}dist-packages:{} '.format(
            self.client.version_dir, idp)
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
        ret += '-v {}backup_dir:{} '.format(self.client.base_dir,
                                            IN_BACKUP_DIR)
        return ret

        return ret

    def stop_environment(self, client_name):
        self._client = Client(self, client_name)
        ret = []

        img2 = 'pg-{}'.format(self.client.name)
        images = []
        if self.client.get_image('aeroo'):
            images.append('aeroo')

        images.append(img2)
        for image in images:
            cmd = Command(
                self,
                command='sudo docker stop {}'.format(image),
                usr_msg='Stopping image {} please wait...'.format(image),
            )
            ret.append(cmd)

        for image in images:
            cmd = Command(
                self,
                command='sudo docker rm {}'.format(image),
                usr_msg='Removing image {}'.format(image),
            )
            ret.append(cmd)

        if self.debug:
            cmd = Command(
                self,
                command='sudo docker rm -f {}'.format('wdb'),
                usr_msg='Removing image {}'.format('wdb'),
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
        command += '--name pg-{} '.format(self.client.name)
        command += image.name

        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)

        ##################################################################
        # Launching aeroo Image
        ##################################################################

        image = self.client.get_image('aeroo')
        if image:
            msg = 'Starting aeroo image'
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

        ##################################################################
        # Launching wdb Image if debug
        ##################################################################
        if self.debug:
            msg = 'Starting wdb image'
            command = 'sudo docker run -d '
            command += '-p 1984:1984 '
            command += '--name=wdb '
            command += 'kozea/wdb:3.2.5'
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
            command='sudo docker stop {}'.format(client_name),
            usr_msg='Stopping image {} please wait...'.format(client_name),
        )
        ret.append(cmd)
        cmd = Command(
            self,
            command='sudo docker rm {}'.format(client_name),
            usr_msg='Removing image {}'.format(client_name),
        )
        ret.append(cmd)

        if self.nginx:
            cmd = Command(
                self,
                command='sudo docker rm -f nginx',
                usr_msg='Killing image nginx',
            )
            ret.append(cmd)

        return ret

    def server_help(self, client_name):
        ret = []
        self._client = Client(self, client_name)

        command = 'sudo docker run --rm -it '
        #        command += self._add_normal_mountings()
        command += '--link pg-{}:db '.format(self.client.name)
        command += '--name help '
        command += '{} '.format(self.client.get_image('odoo').name)
        command += '-- '
        command += '--help '

        cmd = Command(
            self,
            command=command,
            usr_msg='Getting odoo help',
        )
        ret.append(cmd)
        return ret

    def set_config_environment(self):
        ret = []

        command = '-e SERVER_WIDE_MODULES=web,web_kanban,server_mode,' \
                  'database_tools '

        # You should use 2 worker threads + 1 cron thread per available CPU,
        # and 1 CPU per 10 concurent users. Make sure you tune the memory
        # limits and cpu limits in your configuration file.
        if self.debug:
            command += '-e WORKERS=0 '
        else:
            command += '-e WORKERS=3 '

        # number of workers dedicated to cron jobs. Defaults to 2. The workers
        # are threads in multithreading mode and processes in multiprocessing
        # mode.
        command += '-e MAX_CRON_THREADS=1 '

        # Number of requests a worker will process before being recycled and
        # restarted. Defaults to 8196
        # command += '--limit-request 8196 '

        # Maximum allowed virtual memory per worker. If the limit is exceeded,
        # the worker is killed and recycled at the end of the current request.
        # Defaults to 640MB
        # command += '--limit-memory-soft 640000000 '

        # Hard limit on virtual memory, any worker exceeding the limit will be
        # immediately killed without waiting for the end of the current request
        # processing. Defaults to 768MB.
        # command += '--limit-memory-hard 760000000 '

        # Prevents the worker from using more than CPU seconds for each
        # request. If the limit is exceeded, the worker is killed. Defaults
        # to 60.
        command += '-e LIMIT_TIME_CPU=600 '

        # Prevents the worker from taking longer than seconds to process a
        # request. If the limit is exceeded, the worker is killed. Defaults to
        # 120. Differs from --limit-time-cpu in that this is a "wall time"
        # limit including e.g. SQL queries.
        command += '-e LIMIT_TIME_REAL=120 '

        return command

    def run_client(self, client_name, write_config=False):

        self._client = Client(self, client_name)
        ret = []

        if write_config:
            msg = 'Writing config file for client {}'.format(client_name)
        else:
            msg = 'Starting image for client {} on port {}'.format(
                client_name, self.client.port)

        if write_config:
            command = 'sudo docker run --rm '
        else:
            if self.debug:
                command = 'sudo docker run --rm -it '
            else:
                command = 'sudo docker run -d '

        if self.client.get_image('aeroo'):
            command += '--link aeroo:aeroo '

        # open link to wdb image
        if self.debug:
            command += '--link wdb '

        # si tenemos nginx o si estamos escribiendo la configuracion no hay
        # que exponer los puertos
        if not (self.nginx or write_config):
            command += '-p {}:8069 '.format(self.client.port)
            command += '-p 8072:8072 '

        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings(self.client.numeric_ver)

        command += '--link pg-{}:db '.format(self.client.name)

        if not (self.debug or write_config):
            command += '--restart=always '

        # si estamos escribiendo el config no le ponemos el nombre para que
        # pueda correr aunque este levantado el cliente
        if not write_config:
            command += '--name {} '.format(self.client.name)

        if write_config:
            command += self.set_config_environment()
        else:
            command += '-e ODOO_CONF=/dev/null '

        # si estamos en modo debug agregarlo al nombre de la imagen
        if self.debug:
            command += '-e SERVER_MODE=test '
            command += '-e WDB_SOCKET_SERVER=wdb '
            command += '{}.debug '.format(self.client.get_image('odoo').name)
        else:
            command += '-e SERVER_MODE= '
            command += '{} '.format(self.client.get_image('odoo').name)

        if not self.debug:
            command += '--logfile=/var/log/odoo/odoo.log '
        else:
            command += '--logfile=/dev/stdout '

        if write_config:
            command += '--stop-after-init '

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
            command += self._add_debug_mountings(self.client.numeric_ver)
        command += '--link pg-{}:db '.format(self.client.name)
        command += '-e ODOO_CONF=/dev/null '
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

    def qa(self, client_name, database, module_name, client_test=False):
        """
        Corre un test especifico, los parametros necesarios son:

        :param client_name: parametro -c
        :param database: parametro -d
        :param modules: parametro -m (es una lista)
        :return: lista con los comandos para correr
        """

        # solo para que corran los tests
        if client_test:
            self._client = client_test
        else:
            self._client = Client(self, client_name)
        ret = []

        command = 'sudo docker run --rm -it '
        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings(self.client.numeric_ver)
        command += '--link wdb '  # linkeamos con test y setamos nombre
        command += '-e WDB_SOCKET_SERVER=wdb '
        command += '-e ODOO_CONF=/dev/null '
        command += '--link pg-{}:db '.format(self.client.name)
        command += '{}.debug -- '.format(self.client.get_image('odoo').name)
        command += '-d {} '.format(database)
        command += '--stop-after-init '
        command += '--log-level=test '
        command += '--test-enable '
        command += '-u {} '.format(module_name)

        msg = 'Performing tests on module {} for client {} ' \
              'and database {}'.format(module_name, client_name, database)
        cmd = Command(
            self,
            command=command,
            usr_msg=msg
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
    def nginx(self):
        return self._options['nginx']

    @property
    def postfix(self):
        return self._options['postfix']
