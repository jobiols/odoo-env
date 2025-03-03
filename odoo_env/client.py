import ast
import os

from odoo_env.config import OeConfig
from odoo_env.constants import BASE_DIR
from odoo_env.images import Image, Image2
from odoo_env.messages import Msg
from odoo_env.repos import Repo, Repo2

msg = Msg()


class Client:
    """Clase cliente"""

    def __init__(self, odooenv, name):
        """Busca el cliente en la estructura de directorios, pero si no lo
        encuentra pide un directorio donde esta el repo que lo contiene
        """
        # parent es siempre un objeto OdooEnv
        self._parent = odooenv
        self._name = name
        self._license = False
        self._images = []
        self._repos = []
        self._port = False
        self._version = ""

        # si estamos en test accedo a data
        if name[0:5] in ["test_", "test2"]:
            path = os.path.dirname(os.path.abspath(__file__))
            path = path.replace("odoo_env", "odoo_env/data")
            manifest = self.get_manifest(path)
            OeConfig().save_client_path(name, path)
        else:
            manifest = self.get_manifest(BASE_DIR)
        if not manifest:
            msg.inf(
                f"Can not find client {self._name} in this host installation.\n"
                "We will try in current dir"
            )

            # mantener compatibilidad con python2
            input("Hit Enter to continue or CTRL C to exit")
            manifest, _ = self.get_manifest_from_struct(os.getcwd())
            if not manifest:
                msg.err("Can not find client %s in current dir" % name)

            msg.inf("Client found!")
            msg.inf(
                "Name %s\nversion %s\n"
                % (manifest.get("name"), manifest.get("version"))
            )

        self.check_common(manifest)

        # verificar version del manifiesto
        ver = manifest.get("env-ver", "1")
        if ver == "1":
            self.check_v1(manifest)
            msg.warn("The manifest syntax is deprecated, please upgrade to env-ver 2")
            msg.warn("see documentation at https://jobiols.github.io/odoo-env/")
            msg.warn(" ")
        elif ver == "2":
            self.check_v2(manifest)
        else:
            msg.err(
                "Not supported syntax version in manifest, please set env-ver to "
                "1 or 2"
            )

    def check_v1(self, manifest):
        # Chequar que el manifiesto tenga bien las cosas
        if not manifest.get("docker"):
            msg.err("No images in manifest %s" % self.name)

        if not manifest.get("repos"):
            msg.err("No repos in manifest %s" % self.name)

        # Crear imagenes y repos
        self._repos = []
        for rep in manifest.get("repos"):
            self._repos.append(Repo(rep))

        self._images = []
        for img in manifest.get("docker"):
            self._images.append(Image(img))

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
            self._repos.append(Repo2(rep, self._version, self._parent._options))

        for img in manifest.get("docker-images"):
            self._images.append(Image2(img, self._parent.debug))

        # levantar el nombre del user server
        self._prod_server = manifest.get("prod_server", "ubuntu")

    def check_common(self, manifest):
        self._port = manifest.get("port", 8069)
        self._longpolling_port = manifest.get("longpolling_port", 8072)
        self._external_dependencies = manifest.get("external_dependencies", {})
        ver = manifest.get("version")
        if not ver:
            msg.err(f"No version tag in manifest {self.name}")

        _x = ver.find(".") + 1
        _y = ver[_x:].find(".") + _x
        self._version = ver[0:_y]

        name = manifest.get("name").lower()
        if not self._name == name.split()[0]:
            msg.err(
                f"You intend to install client {self._name} but in manifest, "
                f"the name is {manifest.get('name')}"
            )

        # Tomar los datos para odoo.conf
        if self._parent.debug:
            self.config = manifest.get("config-local", [])
        else:
            self.config = manifest.get("config", [])

    def get_manifest_from_struct(self, path):
        """leer un manifest que esta dentro de una estructura de directorios
        revisar toda la estructura hasta encontrar un manifest.
        devolver el manifest y el path
        """
        for root, dirs, files in os.walk(path):
            set_files = {"__openerp__.py", "__manifest__.py"}.intersection(files)
            for file in list(set_files):
                manifest_file = "%s/%s" % (root, file)
                manifest = self.load_manifest(manifest_file)
                name = manifest.get("name", False)
                if name and name.lower() == self._name:
                    return manifest, root
        return False, False

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
        else:
            # no lo encuentro, busco en toda la estructura de directorios
            manifest, path = self.get_manifest_from_struct(path)
            if manifest:
                # si lo encuentro lo guardo en el archivo para la proxima
                OeConfig().save_client_path(self._name, path)
            # devuelvo el manifiesto o false si no esta
            return manifest

    @staticmethod
    def load_manifest(filename):
        """
        Loads a manifest
        :param filename: absolute filename to manifest
        :return: manifest in dictionary format
        """
        manifest = ""
        with open(filename) as _f:
            for line in _f:
                if line.strip() and line.strip()[0] != "#":
                    manifest += line
            try:
                ret = ast.literal_eval(manifest)
            except Exception:
                return {"name": "none"}
            return ret

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
        """/odoo_ar/odoo-13.0/
        /odoo_ar/odoo-13.0e/
        """
        lic = "e" if self._license == "EE" else ""
        return "%sodoo-%s%s/" % (BASE_DIR, self._version, lic)

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
        """/odoo_ar/odoo-13.0/clientname/
        /odoo_ar/odoo-13.0e/clientname/
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
        return "%snginx/" % BASE_DIR

    @property
    def debug(self):
        return self._parent.debug

    @property
    def prod_server(self):
        return self._prod_server
