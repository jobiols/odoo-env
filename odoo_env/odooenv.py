import os
import pwd

from odoo_env.client import Client
from odoo_env.command import *
from odoo_env.constants import *
from odoo_env.install_actualize import download_manifest_from_github
from odoo_env.messages import Msg


class OdooEnv:
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

    def _get_packs(self):
        """Packs a montar en modo debug segun la version de odoo"""
        ver = self.client.numeric_ver
        packs = ["dist-packages", "dist-local-packages"]
        if ver < 11:
            packs += ["extra-addons"]
        return packs

    def _process_repos(self):
        """Clone or update repos as needed"""
        ret = []
        # do nothing if no-repos option is true

        if self.no_repos:
            return ret

        for repo in self.client.repos:
            ##############################################################
            # Clone repo if does not exist
            ##############################################################
            cmd = CloneRepo(
                self,
                usr_msg=f"cloning {repo.formatted}",
                command=f"git -C {self.client.sources_dir} {repo.clone}",
                args=f"{self.client.sources_dir}{repo.dir_name}",
            )
            ret.append(cmd)

            ##############################################################
            # Update repo if exist
            ##############################################################
            cmd = PullRepo(
                self,
                usr_msg=f"pulling {repo.formatted}",
                command=f"git -C {self.client.sources_dir}{repo.dir_name} {repo.pull}",
                args=f"{self.client.sources_dir}{repo.dir_name}",
            )
            ret.append(cmd)

        return ret

    def backup_list(self, client_name):
        """Listar los archivos disponibles para restore"""
        self._client = Client(self, client_name)
        ret = []

        filenames = []
        # walk the backup dir
        for root, dirs, files in os.walk(self.client.backup_dir):
            for filedesc in files:
                filename, file_extension = os.path.splitext(filedesc)
                if file_extension == ".zip":
                    filenames.append(filedesc)

        if len(filenames) > 0:
            filenames.sort()
            msg = "List of available backups for client %s\n\n" % client_name
            for filedesc in filenames:
                msg += filedesc + "\n"
        else:
            msg = "There are no files to restore"

        cmd = MessageOnly(
            self,
            command=False,
            usr_msg=msg,
        )
        ret.append(cmd)
        return ret

    def make_scp_command(self, client_name, backup_file):
        """Crea el comando para bajar el archivo desde el server"""
        cli = Client(self, client_name)
        if backup_file:
            # Bajar el backup backup_file del server
            cmd = f"scp {cli.prod_server}:{cli.server_backup_dir}{backup_file} {cli.backup_dir}server_bkp.zip"
        else:
            # bajar el ultimo archivo del server
            _file = f"ssh {cli.prod_server} ls -t {cli.server_backup_dir} | head -1"
            cmd = f"scp {cli.prod_server}:{cli.server_backup_dir}$({_file}) {cli.backup_dir}server_bkp.zip"
        return cmd

    def restore(
        self,
        client_name,
        database=False,
        backup_file=False,
        no_deactivate=False,
        from_server=False,
    ):
        """Restaurar un backup desde el directorio backup_dir o desde el server de
        produccion
        """
        self._client = Client(self, client_name)
        ret = []

        msg = f"Restoring database {database} "
        if backup_file:
            msg += f"from backup {backup_file} "
        else:
            msg += "from newest backup "

        if not no_deactivate and self._client.debug:
            msg += "and performing deactivation "

        if from_server:
            command = self.make_scp_command(client_name, backup_file)
            cmd = Command(self, command=command, usr_msg="Downloading server backup")
            ret.append(cmd)

        command = "sudo docker run --rm -i "
        command += f"--link pg-{client_name}:db "
        command += f"-v {self.client.backup_dir}:/backup "
        command += f"-v {self.client.base_dir}data_dir/filestore:/filestore "
        command += f"--env NEW_DBNAME={database} "
        if backup_file and not from_server:
            command += f"--env ZIPFILE={backup_file} "
        if from_server and self._client.debug:
            command += "--env ZIPFILE=server_bkp.zip "
        if not no_deactivate and self._client.debug:
            command += "--env DEACTIVATE=True "
        command += "jobiols/dbtools:1.3.0 "

        cmd = Command(
            self,
            command=command,
            usr_msg=msg,
        )
        ret.append(cmd)
        return ret

    def write_config(self, client_name):
        """Sobreescribe el config con los datos que vienen en el manifiesto"""
        self._client = Client(self, client_name)
        ret = []
        if self._client.numeric_ver not in WRITE_CONFIG_OLD_MODE:
            cmd = WriteConfigFile(
                self, args={"client": self._client}, usr_msg="Writing config file"
            )
            ret.append(cmd)
        else:
            ret += self.run_client(client_name, write_config=True)
        return ret

    def pull_images(self, client_name):
        """Forzar la bajada de las imagenes"""
        ret = []
        self._client = Client(self, client_name)
        for image in self._client._images:
            cmd = PullImage(
                self,
                command=f"sudo docker pull {image.name}",
                usr_msg=f"Pulling Image {image.short_name}",
            )
            ret.append(cmd)

        if self.debug:
            cmd = self.do_extract_sources(client_name)
            ret.extend(cmd)
        return ret

    def do_extract_sources(self, client_name):
        """Extrae los fuentes de la imagen debug"""

        self._client = Client(self, client_name)
        ret = []

        ##################################################################
        # removing dirs for extracting sources
        ##################################################################
        for w_dir in self._get_packs():
            r_dir = f"{self.client.version_dir}{w_dir}"
            cmd = RemovedirCommand(
                self,
                command=f"sudo rm -r {r_dir}",
                args=r_dir,
                usr_msg=f"Removing {r_dir}",
            )
            ret.append(cmd)

        ##################################################################
        # create dirs for extracting sources, only for debug
        ##################################################################
        for w_dir in self._get_packs():
            r_dir = f"{self.client.version_dir}{w_dir}"
            cmd = MakedirCommand(self, command=f"mkdir -p {r_dir}", args=r_dir)
            ret.append(cmd)

        ##################################################################
        # change og+w for those dirs
        ##################################################################
        for w_dir in self._get_packs():
            r_dir = f"{self.client.version_dir}{w_dir}"
            cmd = Command(self, command=f"chmod og+w {r_dir}")
            ret.append(cmd)

        ##################################################################
        # Extracting sources
        ##################################################################
        for module in self._get_packs():
            msg = (
                f"Extracting {module} from image {self.client.get_image('odoo').name} "
            )
            command = "sudo docker run -it --rm "
            command += f"--entrypoint=/extract_{module}.sh "
            command += f"-v {self.client.version_dir}{module}/:/mnt/{module} "
            command += f"{self.client.get_image('odoo').name} "

            cmd = ExtractSourcesCommand(
                self,
                command=command,
                args=f"{self.client.version_dir}{module}",
                usr_msg=msg,
            )
            ret.append(cmd)

        # poner permisos de escritura
        for module in self._get_packs():
            r_dir = "%s%s" % (self.client.version_dir, module)
            cmd = Command(
                self,
                command="sudo chmod -R og+w %s/" % r_dir,
                usr_msg="Making writable %s" % r_dir,
            )
            ret.append(cmd)

        # agregar un gitignore
        for module in self._get_packs():
            r_dir = f"{self.client.version_dir}{module}"
            cmd = CreateGitignore(
                self,
                command=f"{r_dir}/.gitignore",
                usr_msg=f"Creating gitignore file in {r_dir}",
            )
            ret.append(cmd)

        for module in self._get_packs():
            # create git repo
            command = f"git -C {self._client.version_dir}{module}/ init "
            cmd = Command(
                self, command=command, usr_msg=f"Init repository for {module}"
            )
            ret.append(cmd)

        for module in self._get_packs():
            command = f"git -C {self._client.version_dir}{module}/ add . "
            cmd = Command(
                self,
                command=command,
                usr_msg=f"Add files to repository for {module}",
            )
            ret.append(cmd)

        for module in self._get_packs():
            command = f"git -C {self._client.version_dir}{module}/ commit -m inicial "
            cmd = Command(
                self, command=command, usr_msg=f"Commit repository for {module}"
            )
            ret.append(cmd)

        return ret

    def install(self, args):
        """Instalacion de cliente,"""
        manifest = download_manifest_from_github(args) if args.install else False

        self._client = Client(self, args.client[0], manifest)
        ret = []

        ##################################################################
        # Create base dir with sudo
        ##################################################################
        msg = f"Installing client {args.client[0]}"
        cmd = MakedirCommand(
            self, command=f"sudo mkdir {BASE_DIR}", args=BASE_DIR, usr_msg=msg
        )
        ret.append(cmd)

        ##################################################################
        # change ownership of base dir
        ##################################################################
        username = pwd.getpwuid(os.getuid()).pw_name
        cmd = Command(self, command=f"sudo chown {username}:{username} {BASE_DIR}")
        ret.append(cmd)

        ##################################################################
        # create all client hierarchy
        ##################################################################
        for w_dir in [
            "postgresql",
            "config",
            "data_dir",
            "backup_dir",
            "log",
            "sources",
        ]:
            r_dir = f"{self.client.base_dir}{w_dir}"
            cmd = MakedirCommand(self, command="mkdir -p %s" % r_dir, args="%s" % r_dir)
            ret.append(cmd)

        ##################################################################
        # change o+w for config, data, log and backup_dir
        ##################################################################
        for w_dir in ["config", "data_dir", "log", "backup_dir"]:
            r_dir = f"{self.client.base_dir}{w_dir}"
            cmd = Command(self, command=f"chmod o+w {r_dir}")
            ret.append(cmd)

        ##################################################################
        # create dirs for nginx if needed
        ##################################################################
        if self.nginx:
            for w_dir in ["cert", "conf", "log"]:
                r_dir = "%s%s" % (BASE_DIR, "nginx/" + w_dir)
                cmd = MakedirCommand(self, command=f"mkdir -p {r_dir}", args=r_dir)
                ret.append(cmd)

        ##################################################################
        # create nginx.conf template if needed. Do not overwrite
        ##################################################################
        if self.nginx:
            r_dir = "%s%s" % (BASE_DIR, "nginx/conf/")
            cmd = CreateNginxTemplate(
                self,
                command="%snginx.conf" % r_dir,
                args="%snginx.conf" % r_dir,
                usr_msg="Generating nginx.conf template",
                client_name=client_name,
            )
            ret.append(cmd)

        ##################################################################
        # Clone or update repos as needed
        ##################################################################

        ret += self._process_repos()

        return ret

    def _add_debug_mountings(self, version):
        iea = IN_EXTRA_ADDONS
        if version in (11, 12):
            idp = IN_DIST_PACKAGES.format("3")
            idlp = IN_DIST_LOCAL_PACKAGES.format("3.5")
        elif version >= 13:
            idp = IN_DIST_PACKAGES.format("3")
            idlp = IN_DIST_LOCAL_PACKAGES.format("3.7")
        else:
            idp = IN_DIST_PACKAGES.format("2.7")
            idlp = IN_DIST_LOCAL_PACKAGES.format("2.7")

        cvd = self.client.version_dir

        ret = f"-v {cvd}extra-addons:{iea} "
        ret += f"-v {cvd}dist-packages:{idp} "
        ret += f"-v {cvd}dist-local-packages:{idlp} "
        return ret

    def _add_normal_mountings(self):
        ret = f"-v {self.client.base_dir}config:{IN_CONFIG} "
        ret += f"-v {self.client.base_dir}data_dir:{IN_DATA} "
        ret += f"-v {self.client.base_dir}log:{IN_LOG} "
        ret += f"-v {self.client.base_dir}sources:{IN_CUSTOM_ADDONS} "
        ret += f"-v {self.client.base_dir}backup_dir:{IN_BACKUP_DIR} "
        return ret

    def stop_environment(self, client_name):
        self._client = Client(self, client_name)
        ret = []

        img2 = f"pg-{self.client.name}"
        images = []
        if self.client.get_image("aeroo"):
            images.append("aeroo")

        images.append(img2)
        for image in images:
            cmd = Command(
                self,
                command=f"sudo docker stop {image}",
                usr_msg=f"Stopping image {image} please wait...",
            )
            ret.append(cmd)

        for image in images:
            cmd = Command(
                self,
                command=f"sudo docker rm {image}",
                usr_msg=f"Removing image {image}",
            )
            ret.append(cmd)

        if self.debug:
            cmd = Command(
                self,
                command="sudo docker rm -f wdb",
                usr_msg="Removing image wdb",
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

        image = self.client.get_image("postgres")
        if image:
            msg = f"Starting postgres image v{image.version}"

        command = "sudo docker run -d "
        if self.debug:
            command += "-p 5432:5432 "
        command += "-e POSTGRES_USER=odoo "
        command += "-e POSTGRES_PASSWORD=odoo "
        command += "-e POSTGRES_DB=postgres "
        command += f"-v {self.client.psql_dir}:/var/lib/postgresql/data "
        command += "--restart=always "
        command += f"--name pg-{self.client.name} "
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

        image = self.client.get_image("aeroo")
        if image:
            msg = "Starting aeroo image"
            command = "sudo docker run -d "
            command += "--name={} ".format(image.short_name)
            command += "--restart=always "
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
            msg = "Starting wdb image"
            command = "sudo docker run -d "
            command += "-p 1984:1984 "
            command += "--name=wdb "
            command += "--restart=always "
            command += "kozea/wdb"
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
            command=f"sudo docker stop {client_name}",
            usr_msg=f"Stopping image {client_name} please wait...",
        )
        ret.append(cmd)
        if self.nginx:
            cmd = Command(
                self,
                command="sudo docker rm -f nginx",
                usr_msg="Killing image nginx",
            )
            ret.append(cmd)

        return ret

    def server_help(self, client_name):
        ret = []
        self._client = Client(self, client_name)

        command = "sudo docker run --rm -it "
        #        command += self._add_normal_mountings()
        command += f"--link pg-{self.client.name}:db "
        command += "--name help "
        command += f"{self.client.get_image('odoo').name} "
        command += "-- "
        command += "--help "

        cmd = Command(
            self,
            command=command,
            usr_msg="Getting odoo help",
        )
        ret.append(cmd)
        return ret

    def set_config_environment(self):
        """Deprecated"""
        command = "-e SERVER_WIDE_MODULES=web,web_kanban,server_mode," "database_tools "

        # You should use 2 worker threads + 1 cron thread per available CPU,
        # and 1 CPU per 10 concurent users. Make sure you tune the memory
        # limits and cpu limits in your configuration file.
        if self.debug:
            command += "-e WORKERS=0 "
        else:
            command += "-e WORKERS=3 "

        # number of workers dedicated to cron jobs. Defaults to 2. The workers
        # are threads in multithreading mode and processes in multiprocessing
        # mode.
        command += "-e MAX_CRON_THREADS=1 "

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
        command += "-e LIMIT_TIME_CPU=600 "

        # Prevents the worker from taking longer than seconds to process a
        # request. If the limit is exceeded, the worker is killed. Defaults to
        # 120. Differs from --limit-time-cpu in that this is a "wall time"
        # limit including e.g. SQL queries.
        command += "-e LIMIT_TIME_REAL=120 "

        return command

    def run_client(self, client_name, write_config=False):
        """El run_client se usa tambien para escribir el config file en las
        versiones definidas en WRITE_CONFIG_OLD_MODE
        """

        self._client = Client(self, client_name)
        ret = []

        if write_config:
            msg = "Writing config file for client %s" % client_name
        else:
            msg = "Starting Odoo image for client %s on port %s" % (
                client_name,
                self.client.port,
            )

        if write_config:
            command = "sudo docker run --rm "
        else:
            if self.debug:
                command = "sudo docker run --rm -it "
            else:
                command = "sudo docker run -d "

        if self.client.get_image("aeroo"):
            command += "--link aeroo:aeroo "

        # open link to wdb image
        if self.debug:
            command += "--link wdb "

        # si tenemos nginx o si estamos escribiendo la configuracion no hay
        # que exponer los puertos.
        if not (self.nginx or write_config):
            command += "-p %s:8069 " % self.client.port
            command += "-p %s:8072 " % self.client.longpolling_port

        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings(self.client.numeric_ver)

        if self.client.get_image("postgres"):
            command += "--link pg-%s:db " % self.client.name

        if not (self.debug or write_config):
            command += "--restart=always "

        # si estamos escribiendo el config no le ponemos el nombre para que
        # pueda correr aunque este levantado el cliente
        if not write_config:
            command += "--name %s " % self.client.name

        if write_config:
            command += self.set_config_environment()
        else:
            command += "-e ODOO_CONF=/dev/null "

        # si estamos en modo debug agregarlo el WDB
        if self.debug:
            command += "-e WDB_SOCKET_SERVER=wdb "

        command += f"{self.client.get_image('odoo').name} "

        if not self.debug:
            command += "--logfile=/var/log/odoo/odoo.log "
        else:
            command += "--logfile=/dev/stdout "

        if write_config:
            command += "--stop-after-init "

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
            msg = "Starting nginx reverse proxy"
            image = self.client.get_image("nginx")
            if not image:
                Msg().err("There is no nginx image on this proyect")

            nginx_dir = self.client.nginx_dir
            command = "sudo docker run -d "
            command += "-v {}conf:/etc/nginx/conf.d:ro ".format(nginx_dir)
            command += "-v {}data_dir/letsencrypt:/etc/letsencrypt ".format(
                self.client.base_dir
            )
            command += "-v {}log:/var/log/nginx/ ".format(nginx_dir)
            command += "-p 80:80 "
            command += "-p 443:443 "
            command += "--name={} ".format(image.short_name)
            command += "--link {}:odoo ".format(client_name)
            command += "--restart=always "

            command += image.name
            cmd = Command(
                self,
                command=command,
                usr_msg=msg,
            )
            ret.append(cmd)

        return ret

    def update(self, client_name, database, modules):
        self._client = Client(self, client_name)
        ret = []

        command = "sudo docker run --rm -it "
        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings(self.client.numeric_ver)
        command += "--link pg-{}:db ".format(self.client.name)
        command += "-e ODOO_CONF=/dev/null "
        command += "{} -- ".format(self.client.get_image("odoo").name)
        command += "--stop-after-init "
        command += "--logfile=false "
        command += "-d {} ".format(database)
        command += "-u {} ".format(", ".join(modules))

        cmd = Command(
            self,
            command=command,
            usr_msg="Performing update of {} on database {}".format(
                ", ".join(modules), database
            ),
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

        command = "sudo docker run --rm -it "
        command += self._add_normal_mountings()
        if self.debug:
            command += self._add_debug_mountings(self.client.numeric_ver)
        command += "--link wdb "
        command += "-e WDB_SOCKET_SERVER=wdb "
        command += "-e ODOO_CONF=/dev/null "
        command += f"--link pg-{self.client.name}:db "
        command += f"{self.client.get_image('odoo').name} -- "
        command += f"-d {database} "
        command += "--stop-after-init "
        command += "--log-level=test "
        command += "--test-enable "
        command += f"-u {module_name} "

        msg = f"Performing tests on module {module_name} for client {client_name} and database {database}"

        cmd = Command(self, command=command, usr_msg=msg)
        ret.append(cmd)
        return ret

    @property
    def client(self):
        return self._client

    @property
    def debug(self):
        return self._options["debug"]

    @property
    def verbose(self):
        return self._options["verbose"]

    @property
    def no_repos(self):
        return self._options["no-repos"]

    @property
    def nginx(self):
        return self._options["nginx"]

    @property
    def force_create(self):
        return self._options["force-create"]
