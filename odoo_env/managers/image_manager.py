from odoo_env.client import Client
from odoo_env.command import Command
from odoo_env.services.docker_client import DockerClient
from odoo_env.services.system import SystemClient


class ImageManager:
    def __init__(self, parent, client_name):
        self.parent = parent
        self.client = Client(parent, client_name)
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
        # removing dirs
        for w_dir in self.parent.get_packs():
            r_dir = f"{self.parent._client.version_dir}{w_dir}"
            cmd_list = self.system_client.get_rm_command(r_dir, recursive=True)
            cmd = Command(self.parent, command=cmd_list, usr_msg=f"Removing {r_dir}")
            ret.append(cmd)

        # create dirs
        for w_dir in self.parent.get_packs():
            r_dir = f"{self.client.version_dir}{w_dir}"
            cmd_list = self.system_client.get_mkdir_command(r_dir)
            cmd = Command(self.parent, command=cmd_list)
            ret.append(cmd)

        # chmod
        for w_dir in self.parent.get_packs():
            r_dir = f"{self.client.version_dir}{w_dir}"
            cmd_list = self.system_client.get_chmod_command(r_dir, "og+w", sudo=True)
            cmd = Command(self.parent, command=cmd_list)
            ret.append(cmd)

        # extract
        for module in self.parent.get_packs():
            msg = (
                f"Extracting {module} from image {self.client.get_image('odoo').name} "
            )

            # This is a complex docker run command.
            # sudo docker run -it --rm --entrypoint=/extract_{module}.sh -v ...

            volumes = {
                f"{self.client.version_dir}{module}/": {"bind": f"/mnt/{module}"}
            }

            cmd_list = self.docker_client.get_run_command(
                self.client.get_image("odoo").name,
                interactive=True,
                remove=True,
                entrypoint=f"/extract_{module}.sh",
                volumes=volumes,
            )

            cmd = Command(self.parent, command=cmd_list, usr_msg=msg)
            ret.append(cmd)

        # chmod recursive
        for module in self.parent.get_packs():
            r_dir = f"{self.client.version_dir}{module}"
            cmd_list = self.system_client.get_chmod_command(
                f"{r_dir}/", "o+w", recursive=True, sudo=True
            )
            cmd = Command(
                self.parent, command=cmd_list, usr_msg=f"Making writable {r_dir}"
            )
            ret.append(cmd)

        return ret
