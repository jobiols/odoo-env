import ast
import os
from pathlib import Path

from odoo_env.config import OeConfig
from odoo_env.constants import BASE_DIR
from odoo_env.images import Image2
from odoo_env.messages import Msg
from odoo_env.repos import Repo2

msg = Msg()


class Client:
    """Clase cliente"""

    def __init__(self, odooenv, name: str):
        self._parent = odooenv
        self._name = name
        self._license = None
        self._images = []
        self._repos = []
        self._port = None
        self._version = None

        # Caso especial para test
        if name.startswith(("test_", "test2")):
            root = Path(__file__).resolve().parent
            path = root / "data"
            manifest = self.get_manifest(path)
            OeConfig().save_client_path(name, str(path))
        else:
            manifest = self.get_manifest(Path(BASE_DIR))

        # Si no lo encontró, buscar en el directorio actual
        if not manifest:
            msg.inf(
                f"Can not find client {self._name} in this host installation.\n"
                "We will try in current dir"
            )

            manifest, root = self.get_manifest_from_struct(Path.cwd())

            if not manifest:
                msg.err(f"Can not find client {name} in current dir")

            msg.inf("Client found!")
            msg.inf(f"Name {manifest.get("name")}\nversion {manifest.get("version")}\n")

        self.check_common(manifest)

        # Validar sintaxis env-ver (solo versión 2)
        ver = manifest.get("env-ver", "2")

        if ver != "2":
            msg.err(
                f"Manifest syntax '{ver}' is not supported.\n"
                f"Only env-ver=2 is allowed."
            )

        # Procesar sintaxis v2
        self.check_v2(manifest)

    def check_v2(self, manifest):
        # Chequar que el manifiesto tenga bien las cosas
        if not manifest.get("docker-images"):
            msg.err(f"No images in manifest {self.name} please add a docker-images key")

        if not manifest.get("git-repos"):
            msg.err(f"No repos in manifest {self.name} please add a git-repos key")

        # leer si es enterprise o community, default community
        self._license = manifest.get("odoo-license", "CE")

        if self._license not in {"EE", "CE"}:
            msg.err("License must be EE or CE")

        # Crear imagenes y repos
        for rep in manifest.get("git-repos"):
            self._repos.append(Repo2(rep, self._version))

        for img in manifest.get("docker-images"):
            self._images.append(Image2(img, OeConfig().debug))

        # levantar el nombre del user server
        self._prod_server = manifest.get("prod_server", "ubuntu")

    @staticmethod
    def parse_odoo_version(ver: str) -> str:
        """
        Recibe algo como '17.0.1.0.0'
        Devuelve '17.0' validando el formato.
        """
        parts = ver.split(".")

        # Odoo standard version expects 5 numeric segments
        if len(parts) != 5:
            msg.err(
                f"Invalid version format '{ver}'. "
                "Expected: MAJOR.MINOR.X.Y.Z  (example: 17.0.1.0.0)"
            )

        major, minor, _, _, _ = parts

        # All segments must be numeric
        if not all(p.isdigit() for p in parts):
            msg.err(f"Invalid version '{ver}', all segments must be numeric")

        # Odoo core rule: MINOR must always be '0'
        if minor != "0":
            msg.err(f"Odoo minor version must be '0', got '{minor}' in '{ver}'")

        return f"{major}.{minor}"

    def check_common(self, manifest):
        # Puertos
        self._port = manifest.get("port", 8069)
        self._longpolling_port = manifest.get("longpolling_port", 8072)

        # Dependencias externas
        self._external_dependencies = manifest.get("external_dependencies", {})

        # Versión (obligatoria)
        ver = manifest.get("version")
        if not ver:
            msg.err(f"No version tag in manifest '{self.name}'")

        # Validar y extraer versión Odoo estándar
        self._version = self.parse_odoo_version(ver)

        # Validar nombre del cliente
        name = manifest.get("name", "").lower()
        if not name:
            msg.err(f"No name in manifest for client '{self._name}'")

        manifest_name = name.split()[0]
        if self._name != manifest_name:
            msg.err(
                f"You intend to install client '{self._name}' but manifest "
                f"name is '{manifest.get('name')}'"
            )

        # Cargar configuración para odoo.conf
        if OeConfig().debug:
            self.config = manifest.get("config-local", [])
        else:
            self.config = manifest.get("config", [])

    def get_manifest_from_struct(
        self, path: Path
    ) -> tuple[dict[str, object] | None, str | None]:
        """
        Recorrer recursivamente un directorio buscando un __manifest__.py.
        Devuelve (manifest_dict, path) o (None, None)
        """

        if not path.exists():
            return None, None

        for root, _, files in os.walk(path):
            if "__manifest__.py" not in files:
                continue

            manifest_file = Path(root) / "__manifest__.py"
            manifest = self.load_manifest(manifest_file)

            # Verificar que sea un dict válido
            if not isinstance(manifest, dict):
                continue

            name = manifest.get("name")

            # Validar nombre
            if isinstance(name, str) and name.lower() == self._name:
                return manifest, root  # root = str desde os.walk

        return None, None

    def get_manifest(self, path):
        """
        :param path: path base para buscar el cliente
        :return: manifiesto del cliente
        """
        # traer el path al cliente de la configuracion
        client_path = OeConfig().get_client_path(self._name)
        # si lo encuentro traigo el manifest rapidamente con el path
        if client_path:
            manifest, _ = self.get_manifest_from_struct(client_path)
            return manifest

        # no lo encuentro, busco en toda la estructura de directorios
        manifest, path = self.get_manifest_from_struct(path)
        if manifest:
            # si lo encuentro lo guardo en el archivo para la proxima
            OeConfig().save_client_path(self._name, path)
        # devuelvo el manifiesto o false si no esta
        return manifest

    @staticmethod
    def load_manifest(filename: str) -> dict[str, object]:
        """
        Loads a manifest
        :param filename: absolute filename to manifest
        :return: manifest in dictionary format
        """
        path = Path(filename)
        if not path.is_file():
            return {"name": "none"}

        try:
            # Leer todas las líneas no vacías ni comentadas
            text = "\n".join(
                line
                for line in path.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            )

            # Convertir a dict seguro
            return ast.literal_eval(text)

        except Exception:
            return {"name": "none"}

    def image(self, image_name):
        for img_dict in self._images:
            if img_dict.get("name") == image_name:
                img = img_dict.get("img")
                ver = img_dict.get("ver")
                ret = img_dict.get("usr")
                if img:
                    ret += "/" + img
                if ver:
                    ret += ":" + ver
                return ret
        msg.err(f"There is no {image_name} image found in this manifest")

    def get_image(self, value):
        for image in self._images:
            if image.short_name == value:
                return image
        return False

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def numeric_ver(self):
        return float(self.version[0:2])

    @property
    def repos(self):
        return self._repos

    @property
    def images(self):
        return self._images

    @property
    def port(self):
        return self._port

    @property
    def external_dependencies(self):
        return self._external_dependencies

    @property
    def longpolling_port(self):
        return self._longpolling_port

    @property
    def version_dir(self):
        """
        /odoo_ar/odoo-18.0/
        /odoo_ar/odoo-18.0e/
        """
        lic = "e" if self._license == "EE" else ""
        return f"{BASE_DIR}odoo-{self._version}{lic}/"

    @property
    def server_version_dir(self):
        """/odoo_ar/odoo-13.0/
        /odoo_ar/odoo-13.0e/
        Esta funcion no tiene que tomar BASE_DIR porque en el servidor es siempre
        /odoo_ar/
        """
        lic = "e" if self._license == "EE" else ""
        return f"/odoo_ar/odoo-{self._version}{lic}/"

    @property
    def base_dir(self):
        """
        /odoo_ar/odoo-18.0/clientname/
        /odoo_ar/odoo-18.0e/clientname/
        """
        return f"{self.version_dir}{self._name}/"

    @property
    def server_base_dir(self):
        """/odoo_ar/odoo-13.0/clientname/
        /odoo_ar/odoo-13.0e/clientname/
        """
        return f"{self.server_version_dir}{self._name}/"

    @property
    def backup_dir(self):
        """/odoo_ar/odoo-13.0/clientname/backup_dir/"""
        return self.base_dir + "backup_dir/"

    @property
    def server_backup_dir(self):
        """/odoo_ar/odoo-13.0/clientname/backup_dir/"""
        return f"{self.server_base_dir}backup_dir/"

    @property
    def sources_dir(self):
        """/odoo_ar/odoo-13.0/clientname/sources/"""
        return self.base_dir + "sources/"

    @property
    def psql_dir(self):
        """/odoo_ar/odoo-13.0/clientname/postgresql/"""
        return self.base_dir + "postgresql/"

    @property
    def config_file(self):
        """/odoo_ar/odoo-13.0/clientname/config/odoo.conf"""
        return self.base_dir + "config/odoo.conf"

    @property
    def nginx_dir(self):
        """/odoo_ar/nginx/"""
        return f"{BASE_DIR}nginx/"

    @property
    def debug(self):
        return self._parent.debug

    @property
    def prod_server(self):
        return self._prod_server
