from odoo_env.command import (
    Command,
    CreateNginxTemplate,
    MakedirCommand,
)
from odoo_env.config import OeConfig
from odoo_env.constants import (
    BASE_DIR,
    IN_BACKUP_DIR,
    IN_CONFIG,
    IN_CUSTOM_ADDONS,
    IN_DATA,
    IN_DIST_LOCAL_PACKAGES,
    IN_DIST_PACKAGES,
    IN_EXTRA_ADDONS,
    IN_LOG,
    WDB_IMAGE_16,
    WDB_IMAGE_DEFAULT,
    WDB_IMAGE_NEW,
)
from odoo_env.messages import msg
from odoo_env.services.docker_client import DockerClient
from odoo_env.services.system import SystemClient


class EnvironmentManager:
    def __init__(self, parent):
        self.parent = parent
        self.docker_client = DockerClient()
        self.system_client = SystemClient()

    def install(self):
        ret = []
        msg = f"Installing client {self.parent._client.name}"

        # Base dir
        cmd_list = self.system_client.get_mkdir_command(BASE_DIR)
        ret.append(
            MakedirCommand(self.parent, command=cmd_list, usr_msg=msg, args=BASE_DIR)
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
            r_dir = f"{self.parent._client.base_dir}{w_dir}"
            cmd_list = self.system_client.get_mkdir_command(r_dir)
            ret.append(MakedirCommand(self.parent, command=cmd_list, args=r_dir))

        # Chown pone el owner como 1100 que es lo que hay en la imagen de odoo
        for w_dir in [
            "config",
            "data_dir",
            "log",
        ]:
            r_dir = f"{self.parent._client.base_dir}{w_dir}"
            cmd_list = self.system_client.get_chown_command(
                r_dir, recursive=True, user="1100", group="1100"
            )
            ret.append(Command(self.parent, command=cmd_list))

        # Chmod
        for w_dir in [
            "config",
            "data_dir",
            "log",
            "backup_dir",
        ]:
            r_dir = f"{self.parent._client.base_dir}{w_dir}"
            cmd_list = self.system_client.get_chmod_command(r_dir, "o+w", sudo=True)
            ret.append(Command(self.parent, command=cmd_list))

        # Nginx
        if self.parent.nginx:
            for w_dir in ["cert", "conf", "log"]:
                r_dir = f"{BASE_DIR}nginx/{w_dir}"
                cmd_list = self.system_client.get_mkdir_command(r_dir)
                ret.append(MakedirCommand(self.parent, command=cmd_list, args=r_dir))

            r_dir = f"{BASE_DIR}nginx/conf/"
            ret.append(
                CreateNginxTemplate(
                    self.parent,
                    command=f"{r_dir}nginx.conf",
                    args=f"{r_dir}nginx.conf",
                    usr_msg="Generating nginx.conf template",
                    client_name=self.parent._client.name,
                )
            )

        # Repos
        ret.extend(self.parent._process_repos())

        if OeConfig().debug:
            # Aca se crean los compandos para hacer el exttract souces
            ret.extend(self.parent.do_extract_sources(self.parent._client.name))

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

        # Network TODO
        # Aqui hay que agregar un comando dedicado que en el chequeo verificque si la red existe
        # def ensure_network(self, network: str) -> None:
        #     inspect = subprocess.run(
        #     ["docker", "network", "inspect", network],
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL,
        # )

        cmd_str = self.docker_client.get_network_create_command("odoo-net")
        ret.append(
            Command(
                self.parent,
                command=cmd_str,
                usr_msg="Starting odoo-net network if needed",
            )
        )

        # Postgres
        image = self.parent._client.get_image("postgres")
        if not image:
            msg().err(f"There is no {image.name} image on this proyect")

        msg = f"Starting postgres image {image.version}"

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
            image.name,
            detach=True,
            ports=ports,
            env={"POSTGRES_USER": "odoo", "POSTGRES_PASSWORD": "odoo"},
            restart="unless-stopped",
            name=f"pg-{self.parent._client.name}",
            network="odoo-net",
            volumes=volumes,
        )
        ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))

        # Aeroo
        image = self.parent._client.get_image("aeroo")
        if image:
            msg = "Starting aeroo image"
            cmd_list = self.docker_client.get_run_command(
                image.name, detach=True, name=image.short_name, restart="always"
            )
            ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))

        # WDB
        if self.parent.debug:
            msg = "Starting wdb image"
            wdb_image = WDB_IMAGE_DEFAULT
            if self.parent._client.numeric_ver == 16.0:
                wdb_image = WDB_IMAGE_16
            elif self.parent._client.numeric_ver > 16.0:
                wdb_image = WDB_IMAGE_NEW

            cmd_list = self.docker_client.get_run_command(
                wdb_image,
                detach=True,
                ports={1984: 1984},
                name="wdb",
                restart="unless-stopped",
                network="odoo-net",
            )
            ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))

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
            cmd_list = self.docker_client.get_rm_command("wdb", force=True)
            ret.append(
                Command(self.parent, command=cmd_list, usr_msg="Removing image wdb")
            )

        return ret

    def run_client(self, write_config=False):
        ret = []

        if write_config:
            msg = f"Writing config file for client {self.parent._client.name}"
            detach = False
            interactive = False
            remove = True
        else:
            msg = (
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
        if not (self.parent.nginx or write_config):
            ports[self.parent._client.port] = 8069
            ports[self.parent._client.longpolling_port] = 8072

        # Mountings
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        restart = "unless-stopped" if not (self.parent.debug or write_config) else None
        name = self.parent._client.name if not write_config else None

        env = {}
        if write_config:
            # set_config_environment logic
            env.update(self._get_config_environment())
        else:
            env["ODOO_CONF"] = "/dev/null"

        if self.parent.debug:
            env["WDB_SOCKET_SERVER"] = "wdb"
            env["WDB_NO_BROWSER_AUTO_OPEN"] = "True"

        image = self.parent._client.get_image("odoo").name

        logfile = None
        if not self.parent.debug:
            logfile = "/var/log/odoo/odoo.log"
        else:
            if self.parent._client.numeric_ver < 19.1:
                logfile = "/dev/stdout"

        cmd_list = self.docker_client.get_run_command(
            image,
            detach=detach,
            interactive=interactive,
            remove=remove,
            name=name,
            network="odoo-net",
            ports=ports,
            volumes=volumes,
            links=links,
            restart=restart,
            env=env,
            stop_after_init=write_config,
            logfile=logfile,
            # odoo-bin arg for 19.1+ debug?
            cmd=(
                ["odoo-bin"]
                if self.parent.debug and self.parent._client.numeric_ver >= 19.1
                else None
            ),
            database=self.parent._client.database_default_name,
        )

        ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))

        # Nginx
        if self.parent.nginx:
            ret.extend(self._run_nginx())

        return ret

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

        if self.parent.nginx:
            cmd_list = self.docker_client.get_rm_command("nginx", force=True)
            ret.append(
                Command(self.parent, command=cmd_list, usr_msg="Killing image nginx")
            )
        return ret

    def update(self, database, modules):
        ret = []
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        cmd_list = self.docker_client.get_run_command(
            self.parent._client.get_image("odoo").name,
            interactive=True,
            remove=True,
            network="odoo-net",
            volumes=volumes,
            links={f"pg-{self.parent._client.name}": "db"},
            env={"ODOO_CONF": "/dev/null"},
            stop_after_init=True,
            logfile="false",
            extra_args=["-d", database, "-u", ", ".join(modules)],
        )

        ret.append(
            Command(
                self.parent,
                command=cmd_list,
                usr_msg=f"Performing update of {', '.join(modules)} on database {database}",
            )
        )
        return ret

    def qa(self, database, modules_to_test, client_test=False):
        if client_test:
            self.client = client_test  # This is a bit hacky, adapting to existing logic

        ret = []
        volumes = self._get_normal_mountings()
        if self.parent.debug:
            volumes.update(self._get_debug_mountings())

        cmd_list = self.docker_client.get_run_command(
            self.parent._client.get_image("odoo").name,
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

        msg = (
            f"Performing tests on module {modules_to_test} for client "
            f"{self.parent._client.name} and database {database}"
        )
        ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))
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
        # Logic from _add_debug_mountings
        version = self.parent._client.numeric_ver
        cvd = self.parent._client.version_dir

        if version in {14, 15, 16}:
            return {
                f"{cvd}dist-packages": {"bind": "/usr/lib/python3/dist-packages"},
                f"{cvd}dist-local-packages": {
                    "bind": "/usr/local/lib/python3.9/dist-packages/"
                },
            }
        if version in {17}:
            return {
                f"{cvd}dist-packages": {"bind": "/usr/lib/python3/dist-packages"},
                f"{cvd}dist-local-packages": {
                    "bind": "/usr/local/lib/python3.10/dist-packages/"
                },
            }
        if version in {18}:
            return {
                f"{cvd}dist-packages": {"bind": "/usr/lib/python3/dist-packages"},
                f"{cvd}dist-local-packages": {
                    "bind": "/usr/local/lib/python3.12/dist-packages/"
                },
            }
        if version in {19}:
            return {
                f"{cvd}src": {"bind": "/odoo/odoo-src"},
                f"{cvd}site-packages": {
                    "bind": "/odoo/venv/lib/python3.10/site-packages"
                },
            }

        # Older versions
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

    def _run_nginx(self):
        ret = []
        msg = "Starting nginx reverse proxy"
        image = self.client.get_image("nginx")
        if not image:
            msg().err("There is no nginx image on this proyect")
            return ret

        nginx_dir = self.client.nginx_dir
        volumes = {
            f"{nginx_dir}conf": {"bind": "/etc/nginx/conf.d", "mode": "ro"},
            f"{self.client.base_dir}data_dir/letsencrypt": {"bind": "/etc/letsencrypt"},
            f"{nginx_dir}log": {"bind": "/var/log/nginx/"},
        }

        cmd_list = self.docker_client.get_run_command(
            image.name,
            detach=True,
            ports={80: 80, 443: 443},
            name=image.short_name,
            links={self.parent._client.name: "odoo"},
            restart="always",
            volumes=volumes,
        )
        ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))
        return ret
