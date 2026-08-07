from odoo_env.client import Client
from odoo_env.command import Command
from odoo_env.config import OeConfig
from odoo_env.constants import ODOO_V14_DEBUG_MOUNTS, ODOO_VERSION_MAP
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

    @staticmethod
    def _resolve_extract_targets(version):
        """Devuelve (targets, legacy_dirs) segun la tecnica de la version.

        v14 usa el layout .deb viejo (dist-packages entero); 15-18 usan el
        layout src/lib de ODOO_VERSION_MAP. legacy_dirs son los dirs host del
        OTRO layout, que se limpian al extraer.
        """
        if version == 14:
            return list(ODOO_V14_DEBUG_MOUNTS.items()), ("src", "lib")
        if version == 19:
            return (
                [
                    ("src", "/odoo/odoo-src"),
                    # python3.* (glob): la version de python del venv es un
                    # detalle de la imagen que cambia entre builds (3.10 ->
                    # 3.12 ...). El glob lo resuelve el shell en el extract,
                    # asi que no hay que tocar codigo por cada bump.
                    ("site-packages", "/odoo/venv/lib/python3.*/site-packages"),
                ],
                ("dist-packages", "dist-local-packages", "lib"),
            )
        info = ODOO_VERSION_MAP.get(version)
        if info is None:
            raise ValueError(
                f"extract_sources is only supported for Odoo v14-19, got v{version}"
            )
        return (
            [("src", info.src), ("lib", info.lib)],
            ("dist-packages", "dist-local-packages"),
        )

    def extract_sources(self):
        ret = []
        version = int(self.client.numeric_ver)
        targets, legacy_dirs = self._resolve_extract_targets(version)
        image = self.client.get_image_required("odoo").name
        cvd = self.client.version_dir

        # Cleanup legacy host dirs del layout que NO usa esta version. Usa
        # force=True para ser idempotente / no-op en instalaciones limpias.
        for legacy_dir in legacy_dirs:
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
            ret.append(
                Command(self.parent, command=cmd_list, usr_msg=f"Removing {r_dir}")
            )

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.make_mkdir_command(r_dir)
            ret.append(Command(self.parent, command=cmd_list))

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.get_chmod_command(r_dir, "og+w", sudo=True)
            ret.append(Command(self.parent, command=cmd_list))

        # Sacar los fuentes de la imagen SIN arrancar odoo: `docker run
        # --entrypoint cp` reemplaza el entrypoint de odoo por `cp`, asi que
        # odoo no arranca. El `cp -a` corre DENTRO del contenedor y preserva
        # los symlinks tal cual (docker cp validaba symlinks que escapan del
        # arbol y rompia, p.ej., con babel/global.dat).
        for host_dir, container_src in targets:
            host_dest = f"{cvd}{host_dir}"
            cmd_list = self.docker_client.get_extract_cp_command(
                image, container_src, host_dest
            )
            ret.append(
                Command(
                    self.parent,
                    command=cmd_list,
                    usr_msg=f"Extracting {host_dir} from image {image}",
                )
            )

        for host_dir, _ in targets:
            r_dir = f"{cvd}{host_dir}"
            cmd_list = self.system_client.get_chmod_command(
                f"{r_dir}/", "o+w", recursive=True, sudo=True
            )
            ret.append(
                Command(
                    self.parent, command=cmd_list, usr_msg=f"Making writable {r_dir}"
                )
            )

        return ret
