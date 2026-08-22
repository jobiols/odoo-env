import subprocess
import sys
from pathlib import Path

from odoo_env.client import Client
from odoo_env.command import (
    CloneRepo,
    Command,
    PullRepo,
    TestAllCommand,
    WriteConfigFile,
)
from odoo_env.config import OeConfig
from odoo_env.deploy_keys import deploy_keys
from odoo_env.managers.backup_manager import BackupManager
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.managers.image_manager import ImageManager
from odoo_env.messages import msg
from odoo_env.options import get_param
from odoo_env.qa.config import RunnerConfig
from odoo_env.qa.runner import TestRunner
from odoo_env.services.docker_client import DockerClient, RunSpec


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
        # Seteamos el cliente inicial resolviendo el nombre desde los args.
        # Primer instalación desde `-i <nombre|URL>`: todavía no hay cliente
        # default, así que derivamos el nombre desde el valor de -i y dejamos
        # que Client.__init__ lo ajuste al nombre real del manifiesto (y lo
        # persista). Sin esto, get_param aborta con "No default client set".
        if isinstance(args.install, str) and args.install and not args.client:
            client_name = args.install
        else:
            client_name = get_param(args, "client")
        self._client = Client(args, name=client_name)

    def build_commands(self):
        # Tabla flag -> builder. El orden define el orden de ejecucion.
        builders = [
            ("install", self.install),
            ("run_env", self.run_environment),
            ("pull_images", self.pull_images),
            ("write_config", self.write_config),
            ("run_cli", self.run_client),
            ("stop_env", self.stop_environment),
            ("stop_cli", self.stop_client),
            ("update", self._build_update),
            ("deploy_keys", self._build_deploy_keys),
            ("modules_to_test", self._build_qa),
            ("server_help", self.server_help),
            ("restore", self._build_restore),
            ("create_test_db", self.create_test_db),
            ("test_all", self._build_test_all),
        ]
        commands = []
        for flag, builder in builders:
            if getattr(self._args, flag):
                commands += builder()
        return commands

    def _build_update(self):
        database = get_param(self._args, "database")
        if not database:
            database = self.client.database_default_name
        # modulos definidos en linea de comandos o todos si no hay ninguno
        modules = get_param(self._args, "module")
        if not modules:
            modules = ["all"]
        return self.update(database, modules)

    def _build_deploy_keys(self):
        conf = OeConfig()
        if not conf.prod:
            msg.err("Must be in prod mode in order to create deploy keys.")
        deploy_keys(self, self.client.name)
        return []

    def _build_qa(self):
        return self.qa(self._args.modules_to_test)

    def _build_restore(self):
        database = get_param(self._args, "database")
        backup_file = get_param(self._args, "backup_file")
        no_deactivate = self._args.no_deactivate
        self._check_backup_available(backup_file)
        return self.restore(self.client.name, database, backup_file, no_deactivate)

    def _build_test_all(self):
        config = RunnerConfig.from_oe(self._client)
        runner = TestRunner(config)
        cmd = TestAllCommand(self, runner=runner)
        return [cmd]

    def _check_backup_available(self, backup_file):
        """
        Guarda para `oe --restore`: verifica que haya algo para restaurar
        antes de armar el comando. Sin esto, si backup_dir no existe o esta
        vacio, el contenedor dbtools explota feo por dentro.
        """
        backup_dir = Path(self.client.backup_dir)

        if not backup_dir.is_dir():
            msg.err(f"Backup directory does not exist: {backup_dir}")

        if backup_file:
            target = backup_dir / backup_file
            if not target.is_file():
                available = sorted(p.name for p in backup_dir.glob("*.zip"))
                hint = (
                    "Available backups: " + ", ".join(available)
                    if available
                    else "No .zip backups in that directory"
                )
                msg.err(f"Backup file not found: {target}\n  {hint}")
            return

        if not list(backup_dir.glob("*.zip")):
            msg.err(
                f"No backup files (*.zip) found in {backup_dir}\n"
                "  Nothing to restore."
            )

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
        database: "str | bool | None" = False,
        backup_file: "str | bool | None" = False,
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

        `database` is passed as a psql variable (-v) and referenced via
        :'dbname' rather than interpolated into the SQL text, so psql
        quotes it as a safe string literal instead of it being pasted
        raw into the query.
        """
        result = subprocess.run(
            [
                "docker",
                "exec",
                f"pg-{self.client.name}",
                "psql",
                "-U",
                "odoo",
                "-v",
                f"dbname={database}",
                "-tAc",
                "SELECT 1 FROM pg_database WHERE datname = :'dbname'",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "1"

    def _installed_modules(self, database: str) -> set[str]:
        """Return names of all installed modules in the given database.

        Queries ir_module_module via docker exec on pg-{client}.
        Returns an empty set on any error (container down, DB missing, etc.).

        Uses the same safe subprocess pattern as _db_exists:
        - subprocess argv list (no shell)
        - capture_output=True, text=True, check=False
        - Fixed SQL text (no interpolation of module names)
        """
        result = subprocess.run(
            [
                "docker",
                "exec",
                f"pg-{self.client.name}",
                "psql",
                "-U",
                "odoo",
                "-d",
                database,
                "-tAc",
                "SELECT name FROM ir_module_module WHERE state = 'installed'",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def _confirm_overwrite(self, subject):
        """Prompt user to confirm overwriting an existing database or file.

        Returns True on 'y'/'yes', raises OeError on no or non-interactive.
        """
        if not sys.stdin.isatty():
            msg.err(
                f"{subject} already exists and stdin is not a terminal.\n"
                "Cannot prompt for confirmation. Remove/rename it manually or "
                "run from an interactive terminal."
            )
        try:
            answer = (
                input(f"{subject} already exists. Overwrite? [y/N]: ").strip().lower()
            )
        except EOFError:
            msg.err(
                f"{subject} already exists and input stream ended.\n"
                "Cannot prompt for confirmation. Aborting."
            )
        return answer in ("y", "yes")

    def create_test_db(self):
        """Create a throwaway test database for the active client.

        Composes discovery, guard checks, seed restore, and module install
        into a flat list of Command objects.

        Order: discovery → zero-module guard → seed guard →
               db-exists confirm → cp → restore → rm → install (-i)
        """
        modules_dir = self.client.custom_modules_dir
        modules = EnvironmentManager.discover_modules_in(modules_dir)
        if not modules:
            msg.err(
                f"No module found in '{modules_dir}'. "
                "That directory must contain at least one subdirectory "
                "with an __manifest__.py file."
            )

        database = f"{self.client.name}_test"

        # Guard: seed database must exist. Checked before the (interactive)
        # db-exists confirm below, so a missing seed fails fast instead of
        # prompting the user first and only then reporting the real problem.
        seed_path = Path(self.client.backup_dir) / "bkp_test" / "test.zip"
        if not seed_path.is_file():
            msg.err(
                f"Seed database not found at {seed_path}. "
                "Cannot create test database."
            )

        # Guard: confirm overwrite if target DB already exists
        if self._db_exists(database):
            if not self._confirm_overwrite(f"Database '{database}'"):
                msg.err("Aborted by user. Test database was not modified.")

        commands = []

        # Step 1: Copy seed to backup_dir
        backup_dir = Path(self.client.backup_dir)

        # Guard: don't silently clobber a real backup that happens to be
        # named test.zip. The staging copy below is written to that exact
        # path and removed once the restore is done, so an unrelated file
        # with the same name would otherwise be destroyed with no warning.
        staging_path = backup_dir / "test.zip"
        if staging_path.exists():
            if not self._confirm_overwrite(f"'{staging_path}'"):
                msg.err(f"Aborted by user. '{staging_path}' was not modified.")

        commands.append(
            Command(
                self,
                command=[
                    "cp",
                    str(backup_dir / "bkp_test" / "test.zip"),
                    str(backup_dir / "test.zip"),
                ],
                usr_msg="Copying seed database",
            )
        )

        # Step 2: Restore seed into test database
        commands += BackupManager(self, self.client.name).restore(
            database=database, backup_file="test.zip", no_deactivate=True
        )

        # Step 3: Remove temporary copy
        commands.append(
            Command(
                self,
                command=["rm", str(backup_dir / "test.zip")],
                usr_msg="Removing temporary seed copy",
            )
        )

        # Step 4: Install all discovered modules with -i
        env_mgr = EnvironmentManager(self)
        commands += env_mgr._build_module_command(database, modules, "-i")

        return commands

    def do_extract_sources(self):
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
        dc = DockerClient()
        cmd_list = dc.get_run_command(
            RunSpec(
                self.client.get_image_required("odoo").name,
                entrypoint="odoo",
                remove=True,
                name="help",
                cmd=["--help"],
            )
        )
        return [Command(self, command=cmd_list, usr_msg="Getting odoo help")]

    def run_client(self, write_config=False):
        return EnvironmentManager(self).run_client(write_config)

    def update(self, database, modules):
        #        self._client = Client(self, client_name)
        return EnvironmentManager(self).update(database, modules)

    def qa(self, modules_to_test):
        """
        Corre un test especifico, los parametros necesarios son:

        :param modules_to_test: parametro -m (es una lista)
        :return: lista con los comandos para correr
        """
        database = f"{self._client.name}_test"

        # Step 1: Module resolution
        if modules_to_test == "all":
            modules_list = TestRunner.discover_test_modules()
            if not modules_list:
                msg.err(
                    "No testable modules found in the current directory. "
                    "'oe -Q all' requires at least one module with a tests/ "
                    "directory."
                )
        else:
            modules_list = [m.strip() for m in modules_to_test.split(",")]

            # Step 2: On-disk guard (skip for "all")
            on_disk = set(
                EnvironmentManager.discover_modules_in(self.client.custom_modules_dir)
            )
            unknown = set(modules_list) - on_disk
            if unknown:
                msg.err(f"Module(s) not found on disk: {', '.join(sorted(unknown))}")

        # Step 3: DB-exists guard
        if not self._db_exists(database):
            msg.err(
                f"Test database '{database}' does not exist.\n"
                "  Create it first with: oe --create-test-db"
            )

        # Step 4: State query
        installed = self._installed_modules(database)

        # Step 5: Partition
        requested = set(modules_list)
        install_modules = sorted(requested - installed)
        update_modules = sorted(requested & installed)

        # Step 6: Delegate
        return EnvironmentManager(self).qa(database, install_modules, update_modules)

    @property
    def client(self):
        return self._client

    @property
    def debug(self):
        return OeConfig().debug

    @property
    def verbose(self):
        return self._args.verbose
