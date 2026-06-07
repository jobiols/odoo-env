from odoo_env.client import Client
from odoo_env.command import Command
from odoo_env.constants import DBTOOLS_IMAGE
from odoo_env.services.docker_client import DockerClient, RunSpec


class BackupManager:
    def __init__(self, parent, client_name):
        self.parent = parent
        self.client = Client(parent._args, client_name)
        self.docker_client = DockerClient()

    def restore(
        self,
        database: "str | bool | None" = False,
        backup_file: "str | bool | None" = False,
        no_deactivate=False,
    ):
        ret = []
        msg = f"Restoring database {database} "
        if backup_file:
            msg += f"from backup {backup_file} "
        else:
            msg += "from newest backup "

        if not no_deactivate and self.client.debug:
            msg += "and performing deactivation "

        volumes = {
            self.client.backup_dir: {"bind": "/backup"},
            f"{self.client.base_dir}data_dir/filestore": {"bind": "/filestore"},
        }

        env: dict[str, str] = {"NEW_DBNAME": str(database)}

        if backup_file:
            env["ZIPFILE"] = str(backup_file)
        if not no_deactivate:
            env["DEACTIVATE"] = "True"

        cmd_list = self.docker_client.get_run_command(
            RunSpec(
                DBTOOLS_IMAGE,
                remove=True,
                network="odoo-net",
                volumes=volumes,
                env=env,
                links={f"pg-{self.client.name}": "db"},
            )
        )

        cmd = Command(self.parent, command=cmd_list, usr_msg=msg)
        ret.append(cmd)
        return ret
