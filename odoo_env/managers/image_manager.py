from odoo_env.client import Client
from odoo_env.command import Command
from odoo_env.config import OeConfig
from odoo_env.constants import ODOO_VERSION_MAP
from odoo_env.services.docker_client import DockerClient
from odoo_env.services.system import SystemClient


class ImageManager:
    def __init__(self, parent):
        self.parent = parent
        client_name = OeConfig().get_client()
        self.client = Client(parent._args, client_name)
        self.docker_client = DockerClient()
        self.system_client = SystemClient()

    def pull_images(self):
        ret = []
        for image in self.client._images:
            cmd_list = self.docker_client.get_pull_command(image.name)
            cmd = Command(
                self.parent,
                command=cmd_list,
                usr_msg=f"Pulling Image {image.short_name}",
            )
            ret.append(cmd)

        if self.parent.debug:
            ret.extend(self.extract_sources())
        return ret

    def extract_sources(self):
        ret = []
        version = int(self.client.numeric_ver)
        info = ODOO_VERSION_MAP.get(version)
        if info is None:
            raise ValueError(
                f"extract_sources is only supported for Odoo v14-18, got v{version}"
            )

        targets = [("src", info.src), ("lib", info.lib)]
        image = self.client.get_image("odoo").name
        cvd = self.client.version_dir

        # Cleanup legacy host dirs from pre-refactor layout (dist-packages,
        # dist-local-packages). Uses force=True so it is a no-op on fresh
        # installs and idempotent on already-migrated ones.
        for legacy_dir in ("dist-packages", "dist-local-packages"):
            r_dir = f"{cvd}{legacy_dir}"
            cmd_list = self.system_client.get_rm_command(
                r_dir, recursive=True, force=True
            )
            ret.append(
                Command(
                    self.parent,
                    command=cmd_list,
                    usr_msg=f"Removing legacy {r_dir}",
                )
            )

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.get_rm_command(r_dir, recursive=True)
            ret.append(Command(self.parent, command=cmd_list, usr_msg=f"Removing {r_dir}"))

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.make_mkdir_command(r_dir)
            ret.append(Command(self.parent, command=cmd_list))

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.get_chmod_command(r_dir, "og+w", sudo=True)
            ret.append(Command(self.parent, command=cmd_list))

        for host_dir, container_src in targets:
            host_dest = f"{cvd}{host_dir}"
            msg = f"Extracting {host_dir} from image {image}"
            cmd_list = self.docker_client.get_extract_command(image, container_src, host_dest)
            ret.append(Command(self.parent, command=cmd_list, usr_msg=msg))

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.get_chmod_command(
                f"{r_dir}/", "o+w", recursive=True, sudo=True
            )
            ret.append(Command(self.parent, command=cmd_list, usr_msg=f"Making writable {r_dir}"))

        return ret
