from odoo_env.client import Client
from odoo_env.command import (
    CloneRepo,
    Command,
    PullRepo,
    WriteConfigFile,
)
from odoo_env.config import OeConfig
from odoo_env.deploy_keys import deploy_keys
from odoo_env.managers.backup_manager import BackupManager
import subprocess
import sys
from pathlib import Path
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.managers.image_manager import ImageManager
from odoo_env.messages import msg
from odoo_env.options import get_param


class OdooEnv:
    """
    Implementa metodos que corresponden a cada una de las acciones que se
    proveen en la interfase argparse.

    corresponde a una opcion, devuelve una lista de tuplas con accion y
    mensaje. El mensaje puede estar o no.
    Si hay mensaje se muestra antes de ejecutar la accion
    """

    def __init__(self, args):
        self._args = args
        OeConfig(args)
        # Seteamos el cliente inicial resolviendo el nombre desde los args
        client_name = get_param(args, "client")
        self._client = Client(args, name=client_name)

    def build_commands(self):

        commands = []

        if self._args.install:
            commands += self.install()

        if self._args.run_env:
            commands += self.run_environment()

        if self._args.pull_images:
            commands += self.pull_images()

        if self._args.write_config:
            commands += self.write_config()

        if self._args.run_cli:
            commands += self.run_client()

        if self._args.stop_env:
            commands += self.stop_environment()

        if self._args.stop_cli:
            commands += self.stop_client()

        if self._args.update:
            database = get_param(self._args, "database")
            if not database:
                database = self.client.database_default_name
            # trajendo los modulos definidos en linea de comandos o todos si no hay ninguno
            modules = get_param(self._args, "module")
            if not modules:
                modules = ["all"]
            commands += self.update(database, modules)

        if self._args.deploy_keys:
            conf = OeConfig()
            if not conf.prod:
                msg.err("Must be in prod mode in order to create deploy keys.")
            deploy_keys(self, self.client.name)

        if self._args.modules_to_test:
            commands += self.qa(self._args.modules_to_test)

        if self._args.server_help:
            commands += self.server_help()

        if self._args.restore:
            database = get_param(self._args, "database")
            backup_file = get_param(self._args, "backup_file")
            no_deactivate = self._args.no_deactivate
            commands += self.restore(
                self.client.name, database, backup_file, no_deactivate
            )

        if self._args.create_test_db:
            commands += self.create_test_db()

        return commands

    def execute(self, commands):
        for command in commands:
            if command and command.check():
                msg.inf(command.usr_msg)
                command.execute()

        # Si instalamos desde URL, buscar el manifiesto en sources_dir
        # y guardar el path para futuras ejecuciones.
        if isinstance(self._args.install, str):
            self._save_client_path_after_install()

    def _save_client_path_after_install(self):
        """
        Después de instalar desde URL, busca recursivamente el
        __manifest__.py en el directorio de fuentes y guarda el path
        en la configuración para uso futuro.
        """
        sources = Path(self.client.sources_dir)
        if not sources.exists():
            return

        manifest, path = Client._discover_manifest_from_path(sources)
        if manifest and path:
            OeConfig().save_client_path(self.client.name, path)

    def write_config(self):
        """Sobreescribe el odoo.conf config con los datos que vienen en el manifiesto"""
        ret = []
        cmd = WriteConfigFile(
            self, args={"client": self.client}, usr_msg="Writing config file"
        )
        ret.append(cmd)
        return ret

    def get_packs(self):
        """Packs a montar en modo debug segun la version de odoo"""
        ver = self.client.numeric_ver
        if ver < 11:
            return ["dist-packages", "dist-local-packages", "extra-addons"]

        if ver <= 18:
            return ["src", "lib"]

        if ver > 18:
            return ["src", "site-packages"]

    def _process_repos(self):
        """Clone or update repos as needed"""
        ret = []

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

    def restore(
        self,
        client_name,
        database=False,
        backup_file=False,
        no_deactivate=False,
    ):
        """Restaurar un backup desde el directorio backup_dir"""
        return BackupManager(self, client_name).restore(
            database, backup_file, no_deactivate
        )

    def _db_exists(self, database):
        """Check if a database exists in the postgres container.

        Queries pg_database via docker exec on pg-{client}.
        Returns True if the database exists.
        """
        result = subprocess.run(
            ["docker", "exec", f"pg-{self.client.name}",
             "psql", "-U", "odoo", "-tAc",
             f"SELECT 1 FROM pg_database WHERE datname='{database}'"],
            capture_output=True, text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "1"

    def _confirm_overwrite(self, database):
        """Prompt user to confirm overwriting an existing database.

        Returns True on 'y'/'yes', raises OeError on no or non-interactive.
        """
        if not sys.stdin.isatty():
            msg.err(
                f"Database '{database}' already exists and stdin is not a terminal.\n"
                "Cannot prompt for confirmation. Drop the database manually or "
                "run from an interactive terminal."
            )
        try:
            answer = input(
                f"Database '{database}' already exists. Overwrite? [y/N]: "
            ).strip().lower()
        except EOFError:
            msg.err(
                f"Database '{database}' already exists and input stream ended.\n"
                "Cannot prompt for confirmation. Aborting."
            )
        return answer in ("y", "yes")

    def create_test_db(self):
        """Create a throwaway test database for the active client.

        Composes discovery, guard checks, seed restore, and module install
        into a flat list of Command objects.

        Order: discovery → zero-module guard → db-exists confirm →
               seed guard → cp → restore → rm → install (-i)
        """
        modules = EnvironmentManager.discover_modules_in_cwd()
        if not modules:
            msg.err(
                "No module found in the current directory. "
                "The current working directory must contain at least one "
                "subdirectory with an __manifest__.py file."
            )

        database = f"{self.client.name}_test"

        # Guard: confirm overwrite if target DB already exists
        if self._db_exists(database):
            if not self._confirm_overwrite(database):
                msg.err(
                    "Aborted by user. Test database was not modified."
                )

        # Guard: seed database must exist
        seed_path = Path(self.client.backup_dir) / "bkp_test" / "test.zip"
        if not seed_path.is_file():
            msg.err(
                f"Seed database not found at {seed_path}. "
                "Cannot create test database."
            )

        commands = []

        # Step 1: Copy seed to backup_dir
        backup_dir = Path(self.client.backup_dir)
        commands.append(Command(
            self,
            command=["cp", str(backup_dir / "bkp_test" / "test.zip"),
                     str(backup_dir / "test.zip")],
            usr_msg="Copying seed database",
        ))

        # Step 2: Restore seed into test database
        commands += BackupManager(self, self.client.name).restore(
            database=database, backup_file="test.zip", no_deactivate=True
        )

        # Step 3: Remove temporary copy
        commands.append(Command(
            self,
            command=["rm", str(backup_dir / "test.zip")],
            usr_msg="Removing temporary seed copy",
        ))

        # Step 4: Install all discovered modules with -i
        env_mgr = EnvironmentManager(self)
        commands += env_mgr._build_module_command(database, modules, "-i")

        return commands

    def do_extract_sources(self, client_name):
        """Extrae los fuentes de la imagen debug"""
        return ImageManager(self).extract_sources()

    def install(self):
        """Instalacion de cliente,"""
        return EnvironmentManager(self).install()

    def pull_images(self):
        """Forzar la bajada de las imagenes"""
        return ImageManager(self).pull_images()

    def stop_environment(self):
        return EnvironmentManager(self).stop_environment()

    def run_environment(self):
        """
        Crea los comandos para lanzar la BD y el wdb
        :return: devuelve los comandos en una lista
        """
        return EnvironmentManager(self).run_environment()

    def stop_client(self):
        return EnvironmentManager(self).stop_client()

    def server_help(self):
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
        return EnvironmentManager(self).run_client(write_config)

    def update(self, database, modules):
        #        self._client = Client(self, client_name)
        return EnvironmentManager(self).update(database, modules)

    def qa(self, modules_to_test, client_test=False):
        """
        Corre un test especifico, los parametros necesarios son:

        :param client_name: parametro -c
        :param database: parametro -d
        :param modules: parametro -m (es una lista)
        :return: lista con los comandos para correr
        """
        database = f"{self._client.name}_test"
        return EnvironmentManager(self).qa(database, modules_to_test, client_test)

    @property
    def client(self):
        return self._client

    @property
    def debug(self):
        return OeConfig().debug

    @property
    def verbose(self):
        return self._args.verbose
