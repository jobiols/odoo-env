from odoo_env.client import Client
from odoo_env.command import Command
from odoo_env.constants import DBTOOLS_IMAGE
from odoo_env.services.docker_client import DockerClient


class BackupManager:
    def __init__(self, parent, client_name):
        self.parent = parent
        self.client = Client(parent._args, client_name)
        self.docker_client = DockerClient()

    def restore(
        self, database=False, backup_file=False, no_deactivate=False, from_server=False
    ):
        ret = []
        msg = f"Restoring database {database} "
        if backup_file:
            msg += f"from backup {backup_file} "
        else:
            msg += "from newest backup "

        if not no_deactivate and self.client.debug:
            msg += "and performing deactivation "

        if from_server:
            # SCP logic remains as string for now or moved to SystemClient?
            # It uses ssh/scp.
            # I'll keep the logic here but wrap it in Command.
            # Ideally SystemClient handles scp.
            command = self._make_scp_command(backup_file)
            cmd = Command(
                self.parent, command=command, usr_msg="Downloading server backup"
            )
            ret.append(cmd)

        # Docker run for restore
        volumes = {
            self.client.backup_dir: {"bind": "/backup"},
            f"{self.client.base_dir}data_dir/filestore": {"bind": "/filestore"},
        }

        env = {"NEW_DBNAME": database}

        if backup_file and not from_server:
            env["ZIPFILE"] = backup_file
        if from_server and self.client.debug:
            env["ZIPFILE"] = "server_bkp.zip"
        if not no_deactivate:
            env["DEACTIVATE"] = "True"

        cmd_list = self.docker_client.get_run_command(
            DBTOOLS_IMAGE,
            remove=True,
            network="odoo-net",
            volumes=volumes,
            env=env,
            links={f"pg-{self.client.name}": "db"},
        )

        cmd = Command(self.parent, command=cmd_list, usr_msg=msg)
        ret.append(cmd)
        return ret

    def _make_scp_command(self, backup_file):
        if backup_file:
            return (
                f"scp {self.client.prod_server}:{self.client.server_backup_dir}{backup_file} "
                f"{self.client.backup_dir}server_bkp.zip"
            )

        _file = f"ssh {self.client.prod_server} ls -t {self.client.server_backup_dir} | head -1"

        return (
            f"scp {self.client.prod_server}:{self.client.server_backup_dir}$({_file}) "
            f"{self.client.backup_dir}server_bkp.zip"
        )
