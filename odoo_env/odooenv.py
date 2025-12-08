from odoo_env.client import Client
from odoo_env.command import *
from odoo_env.constants import *
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

    def __init__(self, options):
        self._options = options
        self._client = None

    def _get_packs(self):
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
        self._client = Client(self, client_name)
        return ImageManager(self, client_name).pull_images()

    def do_extract_sources(self, client_name):
        """Extrae los fuentes de la imagen debug"""
        self._client = Client(self, client_name)
        return ImageManager(self, client_name).extract_sources()

    def install(self, client_name):
        """Instalacion de cliente,"""
        self._client = Client(self, client_name)
        return EnvironmentManager(self).install()

    def stop_environment(self, client_name):
        self._client = Client(self, client_name)
        return EnvironmentManager(self, client_name).stop_environment()

    def run_environment(self, client_name):
        """
        Crea los comandos para lanzar la BD y el wdb
        :return: devuelve los comandos en una lista
        """
        self._client = Client(self, client_name)
        return EnvironmentManager(self, client_name).run_environment()

    def stop_client(self, client_name):
        self._client = Client(self, client_name)
        return EnvironmentManager(self, client_name).stop_client()

    def server_help(self, client_name):
        self._client = Client(self, client_name)
        # Implement server_help in EnvironmentManager?
        # I missed adding it to EnvironmentManager in previous step.
        # I'll implement it here using DockerClient directly or add it to EnvironmentManager later.
        # For now, I'll implement it here using DockerClient to be consistent with refactor.
        # Or I should add it to EnvironmentManager.
        # I'll add it to EnvironmentManager in a separate edit, or just inline it here using DockerClient.
        # Inline here using DockerClient is fine for now, but better in Manager.
        # I'll leave it as TODO or implement it here.

        # Original logic:
        # command = "sudo docker run --rm -it "
        # command += f"--link pg-{self.client.name}:db "
        # command += "--name help "
        # command += f"{self.client.get_image('odoo').name} "
        # command += "-- "
        # command += "--help "

        from odoo_env.services.docker_client import DockerClient

        dc = DockerClient(sudo=True)
        cmd_list = dc.get_run_command(
            self.client.get_image("odoo").name,
            interactive=True,
            remove=True,
            links={f"pg-{self.client.name}": "db"},
            name="help",
            cmd=["--", "--help"],
        )
        return [Command(self, command=cmd_list, usr_msg="Getting odoo help")]

    def run_client(self, client_name, write_config=False):
        """El run_client se usa tambien para escribir el config file en las
        versiones definidas en WRITE_CONFIG_OLD_MODE
        """
        self._client = Client(self, client_name)
        return EnvironmentManager(self, client_name).run_client(write_config)

    def update(self, client_name, database, modules):
        self._client = Client(self, client_name)
        return EnvironmentManager(self, client_name).update(database, modules)

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
        return EnvironmentManager(self, client_name).qa(
            database, module_name, client_test
        )

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
