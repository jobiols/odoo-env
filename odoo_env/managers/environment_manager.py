import os
from pathlib import Path
from typing import TYPE_CHECKING

from odoo_env.command import (
    Command,
    EnsureNetworkCommand,
    MakedirCommand,
)
from odoo_env.config import OeConfig
from odoo_env.constants import (
    IN_BACKUP_DIR,
    IN_CONFIG,
    IN_CUSTOM_ADDONS,
    IN_DATA,
    IN_DIST_LOCAL_PACKAGES,
    IN_DIST_PACKAGES,
    IN_EXTRA_ADDONS,
    IN_LOG,
    ODOO_V14_DEBUG_MOUNTS,
    ODOO_VERSION_MAP,
    WDB_IMAGE_16,
    WDB_IMAGE_DEFAULT,
    WDB_IMAGE_NEW,
)
from odoo_env.messages import msg
from odoo_env.services.docker_client import DockerClient, RunSpec
from odoo_env.services.system import SystemClient

if TYPE_CHECKING:
    from odoo_env.odooenv import OdooEnv


class EnvironmentManager:
    def __init__(self, parent: "OdooEnv"):
        self.parent = parent
        self._client = parent.client
        self.docker_client = DockerClient()
        self.system_client = SystemClient()

    @staticmethod
    def discover_modules_in_cwd():
        """Scan CWD for immediate subdirectories containing __manifest__.py.

        Does NOT recurse into subdirectories.
        Returns a sorted list of directory names.
        """
        cwd = Path(os.getcwd())
        modules = []
        for entry in cwd.iterdir():
            if entry.is_dir() and (entry / "__manifest__.py").is_file():
                modules.append(entry.name)
        return sorted(modules)

    def install(self):
        ret = []
        step_msg = f"Installing client {OeConfig().client}"
        cmd_list = self.system_client.make_mkdir_command()

        ret.append(
            MakedirCommand(
                self.parent,
                command=cmd_list,
                usr_msg=step_msg,
                args=OeConfig().base_dir,
            )
        )

        # Client hierarchy
        for w_dir in [
            "postgresql",
            "config",
            "data_dir",
            "backup_dir",
            "log",
            "sources",
        ]:
            r_dir = f"{self._client.base_dir}{w_dir}"
            cmd_list = self.system_client.make_mkdir_command(r_dir)
            ret.append(MakedirCommand(self.parent, command=cmd_list, args=r_dir))

        # Chown pone el owner como 1100 que es lo que hay en la imagen de odoo
        for w_dir in [
            "config",
            "data_dir",
            "log",
        ]:
            r_dir = f"{self._client.base_dir}{w_dir}"
            cmd_list = self.system_client.get_chown_command(
                r_dir, owner="1100:1100", recursive=True
            )
            ret.append(Command(self.parent, command=cmd_list))

        # Chmod
        for w_dir in [
            "config",
            "data_dir",
            "log",
            "backup_dir",
        ]:
            r_dir = f"{self._client.base_dir}{w_dir}"
            cmd_list = self.system_client.get_chmod_command(r_dir, "o+w", sudo=True)
            ret.append(Command(self.parent, command=cmd_list))

        # Repos
        ret.extend(self.parent._process_repos())

        return ret

    def run_environment(self):
        """
        Docstring for run_environment

            docker run -d -p 5432:5432 -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo
            -v /odoo/ar/odoo-16.0e/bukito/postgresql/:/var/lib/postgresql/data
            --restart=unless-stopped --name pg-bukito --network odoo-net
            --network-alias db postgres:17.5-alpine



            docker run -d
            -p 5432:5432
            -e POSTGRES_USER=odoo
            -e POSTGRES_PASSWORD=odoo
            --restart unless-stopped
            --name pg-bukito

            --network odoo-net
            -v /odoo/ar/odoo-16.0e/bukito/postgresql/:/var/lib/postgresql/data:rw
            postgres:17.5-alpine

        """

        ret = []

        # Network — create only if absent
        ret.append(
            EnsureNetworkCommand(
                self.parent,
                command=self.docker_client.get_network_create_command("odoo-net"),
                usr_msg="Starting odoo-net network if needed",
                args="odoo-net",
            )
        )

        # Postgres
        image = self.parent._client.get_image("postgres")
        if not image:
            msg.err("There is no postgres image on this project")

        step_msg = f"Starting postgres image {image.version}"

        if image.numeric_ver >= 18:
            volumes = {
                self.parent._client.psql_dir: {
                    "bind": f"/var/lib/postgresql/{image.numeric_ver}/docker"
                }
            }
        else:
            volumes = {
                self.parent._client.psql_dir: {"bind": "/var/lib/postgresql/data"}
            }

        ports = {5432: 5432} if self.parent.debug else None

        cmd_list = self.docker_client.get_run_command(
            RunSpec(
                image.name,
                detach=True,
                ports=ports,
                env={"POSTGRES_USER": "odoo", "POSTGRES_PASSWORD": "odoo"},
                restart="unless-stopped",
                name=f"pg-{self.parent._client.name}",
                network="odoo-net",
                volumes=volumes,
            )
        )
        ret.append(Command(self.parent, command=cmd_list, usr_msg=step_msg))

        # Aeroo
        image = self.parent._client.get_image("aeroo")
        if image:
            step_msg = "Starting aeroo image"
            cmd_list = self.docker_client.get_run_command(
                RunSpec(
                    image.name,
                    detach=True,
                    name=image.short_name,
                    restart="always",
                )
            )
            ret.append(Command(self.parent, command=cmd_list, usr_msg=step_msg))

        # WDB
        if self.parent.debug:
            step_msg = "Starting wdb image"
            wdb_image = WDB_IMAGE_DEFAULT
            if self.parent._client.numeric_ver == 16.0:
                wdb_image = WDB_IMAGE_16
            elif self.parent._client.numeric_ver > 16.0:
                wdb_image = WDB_IMAGE_NEW

            cmd_list = self.docker_client.get_run_command(
                RunSpec(
                    wdb_image,
                    detach=True,
                    ports={1984: 1984},
                    name="wdb",
                    restart="unless-stopped",
                    network="odoo-net",
                )
            )
            ret.append(Command(self.parent, command=cmd_list, usr_msg=step_msg))

        return ret

    def stop_environment(self):
        ret = []
        images = [f"pg-{self.parent._client.name}"]
        if self.parent._client.get_image("aeroo"):
            images.append("aeroo")

        for image in images:
            cmd_list = self.docker_client.get_stop_command(image)
            ret.append(
                Command(
                    self.parent,
                    command=cmd_list,
                    usr_msg=f"Stopping image {image} please wait...",
                )
            )

        for image in images:
            cmd_list = self.docker_client.get_rm_command(image)
            ret.append(
                Command(
                    self.parent, command=cmd_list, usr_msg=f"Removing image {image}"
                )
            )

        if self.parent.debug:
            ret.append(
                Command(
                    self.parent,
                    command=self.docker_client.get_stop_command("wdb"),
                    usr_msg="Stopping image wdb please wait...",
                )
            )
            ret.append(
                Command(
                    self.parent,
                    command=self.docker_client.get_rm_command("wdb"),
                    usr_msg="Removing image wdb",
                )
            )

        return ret

    def run_client(self, write_config=False):
        ret = []

        if write_config:
            step_msg = f"Writing config file for client {self.parent._client.name}"
            detach = False
            interactive = False
            remove = True
        else:
            step_msg = (
                f"Starting Odoo image for client {self.parent._client.name} "
                "on port {self.parent._client.port}"
            )
            detach = not self.parent.debug
            interactive = self.parent.debug
            remove = self.parent.debug

        links = {}
        if self.parent._client.get_image("aeroo"):
            links["aeroo"] = "aeroo"

        links[f"pg-{self.parent._client.name}"] = "db"

        ports = {}
        if not write_config:
            ports[self.parent._client.port] = 8069
            ports[self.parent._client.longpolling_port] = 8072

        # Mountings
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        restart = "unless-stopped" if not (self.parent.debug or write_config) else None
        name = self.parent._client.name if not write_config else None

        cmd_list = self.docker_client.get_run_command(
            RunSpec(
                self.parent._client.get_image_required("odoo").name,
                detach=detach,
                interactive=interactive,
                remove=remove,
                name=name,
                network="odoo-net",
                ports=ports,
                volumes=volumes,
                links=links,
                restart=restart,
                env=self._run_client_env(write_config),
                stop_after_init=write_config,
                logfile=self._run_client_logfile(),
                # odoo-bin arg for 19.1+ debug?
                cmd=(
                    ["odoo-bin"]
                    if self.parent.debug and self.parent._client.numeric_ver >= 19.1
                    else None
                ),
                database=self.parent._client.database_default_name,
            )
        )

        ret.append(Command(self.parent, command=cmd_list, usr_msg=step_msg))

        return ret

    def _run_client_env(self, write_config):
        """Arma el dict de environment para el contenedor de odoo."""
        env = {}
        if write_config:
            env.update(self._get_config_environment())
        else:
            env["ODOO_CONF"] = "/dev/null"

        if self.parent.debug:
            env["WDB_SOCKET_SERVER"] = "wdb"
            env["WDB_NO_BROWSER_AUTO_OPEN"] = "True"
        return env

    def _run_client_logfile(self):
        """Determina el logfile de odoo segun modo debug y version."""
        if not self.parent.debug:
            return "/var/log/odoo/odoo.log"
        if self.parent._client.numeric_ver < 19.1:
            return "/dev/stdout"
        return None

    def stop_client(self):
        ret = []
        cmd_list = self.docker_client.get_stop_command(self.parent._client.name)
        ret.append(
            Command(
                self.parent,
                command=cmd_list,
                usr_msg=f"Stopping image {self.parent._client.name} please wait...",
            )
        )

        return ret

    def _build_module_command(self, database, modules, verb, usr_msg_prefix=None):
        """Build docker run command for -i (install) or -u (update) modules.

        Extracts the shared scaffolding so both update() and create_test_db()
        can reuse the same volume, network, and env configuration.

        Args:
            database: Target database name (e.g., 'dimec_test')
            modules: List of module names to install/update
            verb: '-i' for install or '-u' for update
            usr_msg_prefix: Override the user message prefix.
                            Defaults to 'Installing' for -i, 'Updating' for -u.
        """
        ret = []
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        cmd_list = self.docker_client.get_run_command(
            RunSpec(
                self.parent._client.get_image_required("odoo").name,
                interactive=True,
                remove=True,
                network="odoo-net",
                volumes=volumes,
                links={f"pg-{self.parent._client.name}": "db"},
                env={"ODOO_CONF": "/dev/null"},
                stop_after_init=True,
                logfile="false",
                extra_args=["-d", database, verb, ", ".join(modules)],
            )
        )

        if usr_msg_prefix is None:
            action = "Installing" if verb == "-i" else "Updating"
        else:
            action = usr_msg_prefix

        ret.append(
            Command(
                self.parent,
                command=cmd_list,
                usr_msg=f"{action} {', '.join(modules)} on database {database}",
            )
        )
        return ret

    def update(self, database, modules):
        return self._build_module_command(
            database, modules, "-u", usr_msg_prefix="Performing update of"
        )

    def qa(self, database, modules_to_test):
        ret = []
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        cmd_list = self.docker_client.get_run_command(
            RunSpec(
                self.parent._client.get_image_required("odoo").name,
                interactive=True,
                remove=True,
                network="odoo-net",
                volumes=volumes,
                links={f"pg-{self.parent._client.name}": "db"},
                env={
                    "WDB_SOCKET_SERVER": "wdb",
                    "WDB_NO_BROWSER_AUTO_OPEN": "True",
                    "ODOO_CONF": "/dev/null",
                },
                stop_after_init=True,
                log_level="test",
                test_enable=True,
                extra_args=["-d", database, "-u", modules_to_test],
            )
        )

        step_msg = (
            f"Performing tests on module {modules_to_test} for client "
            f"{self.parent._client.name} and database {database}"
        )
        ret.append(Command(self.parent, command=cmd_list, usr_msg=step_msg))
        return ret

    def _get_normal_mountings(self):
        return {
            f"{self.parent._client.base_dir}config": {"bind": IN_CONFIG},
            f"{self.parent._client.base_dir}data_dir": {"bind": IN_DATA},
            f"{self.parent._client.base_dir}log": {"bind": IN_LOG},
            f"{self.parent._client.base_dir}sources": {"bind": IN_CUSTOM_ADDONS},
            f"{self.parent._client.base_dir}backup_dir": {"bind": IN_BACKUP_DIR},
        }

    def _get_debug_mountings(self):
        version = self.parent._client.numeric_ver
        cvd = self.parent._client.version_dir

        if version == 14:
            # Layout .deb viejo: dist-packages entero (ver ODOO_V14_DEBUG_MOUNTS).
            return {
                f"{cvd}{host}": {"bind": bind}
                for host, bind in ODOO_V14_DEBUG_MOUNTS.items()
            }

        info = ODOO_VERSION_MAP.get(int(version))
        if info is not None:
            return {
                f"{cvd}src": {"bind": info.src},
                f"{cvd}lib": {"bind": info.lib + "/"},
            }
        if version == 19:
            return {
                f"{cvd}src": {"bind": "/odoo/odoo-src"},
                f"{cvd}site-packages": {
                    "bind": "/odoo/venv/lib/python3.10/site-packages"
                },
            }
        if version < 14:
            iea = IN_EXTRA_ADDONS
            idp = IN_DIST_PACKAGES.format("2")
            idlp = IN_DIST_LOCAL_PACKAGES.format("2.7")
            if version in {11, 12}:
                idp = IN_DIST_PACKAGES.format("3")
                idlp = IN_DIST_LOCAL_PACKAGES.format("3.5")
            elif version in {13}:
                idp = IN_DIST_PACKAGES.format("3")
                idlp = IN_DIST_LOCAL_PACKAGES.format("3.7")
            return {
                f"{cvd}dist-packages": {"bind": idp},
                f"{cvd}dist-local-packages": {"bind": idlp},
                f"{cvd}extra-addons": {"bind": iea},
            }
        raise ValueError(f"Unsupported Odoo version: {version}")

    def _get_config_environment(self):
        # Logic from set_config_environment
        env = {
            "SERVER_WIDE_MODULES": "web,web_kanban,server_mode,database_tools",
            "MAX_CRON_THREADS": "1",
            "LIMIT_TIME_CPU": "600",
            "LIMIT_TIME_REAL": "120",
        }
        if self.parent.debug:
            env["WORKERS"] = "0"
        else:
            env["WORKERS"] = "3"
        return env
