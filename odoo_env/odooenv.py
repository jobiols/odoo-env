from odoo_env.client import Client
from odoo_env.command import (
    CloneRepo,
    Command,
    PullRepo,
    WriteConfigFile,
)
from odoo_env.config import OeConfig
from odoo_env.constants import (
    WRITE_CONFIG_OLD_MODE,
)
from odoo_env.managers.backup_manager import BackupManager
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.managers.image_manager import ImageManager


class OdooEnv:
    """
    Implementa metodos que corresponden a cada una de las acciones que se
    proveen en la interfase argparse.

    corresponde a una opcion, devuelve una lista de tuplas con accion y
    mensaje. El mensaje puede estar o no.
    Si hay mensaje se muestra antes de ejecutar la accion
    """

    def __init__(self, args):

        client_name = OeConfig().get_client()
        self._client = Client(self, client_name)
        self._nginx = args.nginx
        self._no_repos = args.no_repos

    def write_config(self):
        """Sobreescribe el odoo.conf config con los datos que vienen en el manifiesto"""
        self._client = Client(self, OeConfig().get_client())
        ret = []
        if self._client.numeric_ver not in WRITE_CONFIG_OLD_MODE:
            cmd = WriteConfigFile(
                self, args={"client": self._client}, usr_msg="Writing config file"
            )
            ret.append(cmd)
        else:
            ret += self.run_client(client_name, write_config=True)
        return ret

    def get_packs(self):
        """Packs a montar en modo debug segun la version de odoo"""
        ver = self.client.numeric_ver
        if ver < 11:
            packs = ["dist-packages", "dist-local-packages", "extra-addons"]
            return packs

        if ver <= 18:
            packs = ["dist-packages", "dist-local-packages"]
            return packs

        if ver > 18:
            packs = ["src", "site-packages"]
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
        return BackupManager(self, client_name).backup_list()

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
        return BackupManager(self, client_name).restore(
            database, backup_file, no_deactivate, from_server
        )

    def do_extract_sources(self, client_name):
        """Extrae los fuentes de la imagen debug"""
        self._client = Client(self, client_name)
        return ImageManager(self).extract_sources()

    def install(self):
        """Instalacion de cliente,"""
        return EnvironmentManager(self).install()

    def pull_images(self):
        """Forzar la bajada de las imagenes"""
        return ImageManager(self).pull_images()

    def stop_environment(self, client_name):
        self._client = Client(self, client_name)
        return EnvironmentManager(self).stop_environment()

    def run_environment(self):
        """
        Crea los comandos para lanzar la BD y el wdb
        :return: devuelve los comandos en una lista
        """
        return EnvironmentManager(self).run_environment()

    def stop_client(self, client_name):
        self._client = Client(self, client_name)
        return EnvironmentManager(self).stop_client()

    def server_help(self, client_name):
        self._client = Client(self, client_name)

        from odoo_env.services.docker_client import DockerClient

        dc = DockerClient()
        cmd_list = dc.get_run_command(
            self.client.get_image("odoo").name,
            entrypoint="odoo",
            remove=True,
            name="help",
            cmd=["--help"],
        )
        return [Command(self, command=cmd_list, usr_msg="Getting odoo help")]

    def run_client(self, write_config=False):
        """El run_client se usa tambien para escribir el config file en las
        versiones definidas en WRITE_CONFIG_OLD_MODE
        """
        self._client = Client(self, OeConfig().get_client)
        return EnvironmentManager(self).run_client(write_config)

    def update(self, client_name, database, modules):
        self._client = Client(self, client_name)
        return EnvironmentManager(self).update(database, modules)

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
        return EnvironmentManager(self).qa(database, module_name, client_test)

    @property
    def client(self):
        return self._client

    @property
    def debug(self):
        return OeConfig().debug

    @property
    def verbose(self):
        return self._options["verbose"]

    @property
    def no_repos(self):
        return self._no_repos

    @property
    def nginx(self):
        return self._nginx

    @property
    def force_create(self):
        return self._options["force-create"]
