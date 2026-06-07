import ast
import difflib
import os
import subprocess
import tempfile
from pathlib import Path

from odoo_env.config import OeConfig
from odoo_env.images import DockerImage
from odoo_env.messages import msg
from odoo_env.repos import GitRepo

# Claves especificas de odoo-env (las que oe lee del manifiesto).
# Si se escriben mal, oe falla en silencio usando el default.
ODOO_ENV_KEYS = frozenset(
    {
        "config",
        "config-local",
        "git-repos",
        "docker-images",
        "odoo-license",
        "env-ver",
        "port",
        "longpolling_port",
        "external_dependencies",
        "prod_server",
    }
)

# Claves estandar de un __manifest__.py de Odoo (el manifiesto es doble:
# vale como modulo Odoo y como manifiesto odoo-env). Se aceptan para no
# marcar como invalidas claves legitimas de Odoo.
ODOO_STANDARD_KEYS = frozenset(
    {
        "name",
        "version",
        "description",
        "author",
        "website",
        "license",
        "category",
        "depends",
        "data",
        "demo",
        "demo_xml",
        "init_xml",
        "update_xml",
        "test",
        "css",
        "js",
        "qweb",
        "images",
        "application",
        "auto_install",
        "installable",
        "summary",
        "sequence",
        "bootstrap",
        "web",
        "web_icon",
        "pre_init_hook",
        "post_init_hook",
        "post_load",
        "uninstall_hook",
        "assets",
        "cloc_exclude",
        "live_test_url",
        "maintainer",
        "maintainers",
        "contributors",
        "support",
        "price",
        "currency",
        "countries",
        "complexity",
        "icon",
        "active",
        "excludes",
    }
)

# Union de todas las claves validas que puede tener el manifiesto.
VALID_MANIFEST_KEYS = ODOO_ENV_KEYS | ODOO_STANDARD_KEYS


class Client:
    """Esta clase representa a un cliente, con su manifiesto, sus imagenes y repositorios."""

    def __init__(self, args, name=None):
        self._name = name or OeConfig().client
        self._args = args
        self._images = []
        self._repos = []

        # Caso especial para test
        if self._name.startswith(("test_", "test2")):
            root = Path(__file__).resolve().parent
            path = root / "data"
            manifest = self.get_manifest(path)
            OeConfig().save_client_path(self.name, str(path))
        elif isinstance(self._args.install, str):
            # Primera instalación desde URL: clonar repo temporalmente,
            # extraer el nombre del proyecto del manifiesto y usarlo
            # como el nuevo cliente default.
            manifest = self._discover_from_url(self._args.install)[0]
            if not manifest:
                msg.err(
                    f"No valid __manifest__.py found in repository "
                    f"'{self._args.install}'"
                )
            # Cambiar al nombre que declara el manifiesto
            new_name = str(manifest.get("name", "")).lower().split()[0]
            if new_name:
                if new_name != self._name:
                    self._name = new_name
                OeConfig().save_client(self._name)
        else:
            manifest = self.get_manifest()

        if not manifest:
            msg.err(f"No manifest found for client '{self._name}'")

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
            self._repos.append(GitRepo(rep, self._version))

        for img in manifest.get("docker-images"):
            self._images.append(DockerImage(img, OeConfig().debug))

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

    @staticmethod
    def validate_manifest_keys(manifest, name):
        """
        Verifica que todas las claves del manifiesto sean validas (claves
        odoo-env o claves estandar de Odoo). Aborta con una sugerencia si
        encuentra una clave desconocida; asi un typo como 'config_local'
        no falla en silencio usando el default.
        """
        candidates = sorted(VALID_MANIFEST_KEYS)
        errors = []
        for key in manifest:
            if key in VALID_MANIFEST_KEYS:
                continue
            match = difflib.get_close_matches(key, candidates, n=1, cutoff=0.6)
            if match:
                errors.append(f"  '{key}' is not valid, did you mean '{match[0]}'?")
            else:
                errors.append(f"  '{key}' is not a recognized manifest key")

        if errors:
            msg.err(f"Invalid keyword(s) in manifest '{name}':\n" + "\n".join(errors))

    def check_common(self, manifest):
        # Validar que no haya claves mal escritas (typos que fallan en silencio)
        self.validate_manifest_keys(manifest, self._name)

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

    @staticmethod
    def _discover_manifest_from_path(
        path: Path,
    ) -> tuple[dict[str, object] | None, str | None]:
        """
        Recorre recursivamente un directorio buscando __manifest__.py
        sin validar el nombre del cliente.
        Devuelve (manifest_dict, path) o (None, None).
        """
        if not path.exists():
            return None, None

        for root, _, files in os.walk(path):
            if "__manifest__.py" not in files:
                continue

            manifest_file = Path(root) / "__manifest__.py"
            manifest = Client.load_manifest(manifest_file)

            if (
                isinstance(manifest, dict)
                and manifest.get("name")
                and manifest.get("env-ver")
            ):
                return manifest, str(manifest_file.parent)

        return None, None

    def _discover_from_url(
        self, url: str
    ) -> tuple[dict[str, object] | None, str | None]:
        """
        Clona un repositorio temporalmente y extrae el manifiesto
        sin validar el nombre del cliente.
        Devuelve (manifest_dict, manifest_dir) o (None, None).
        """
        if not (url.startswith("git@") or url.startswith("https://")):
            msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", "--depth", "1", url, tmpdir], check=True)
            return self._discover_manifest_from_path(Path(tmpdir))

    def get_manifest_from_url(self) -> dict[str, object] | None:
        url = self._args.install
        if not (
            isinstance(url, str)
            and (url.startswith("git@") or url.startswith("https://"))
        ):
            msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")

        manifest, manifest_dir = self._discover_from_url(url)
        if manifest and manifest_dir:
            OeConfig().save_client_path(self._name, manifest_dir)
        return manifest

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
            if isinstance(name, str) and name.lower() != self._name:
                msg.err(f"project name {name} does not match client name {self._name}")

            return manifest, str(manifest_file.parent)

        return None, None

    def get_manifest(self, path=None):
        """
        :param path: path base para buscar el cliente
        :return: manifiesto del cliente
        """
        # Si no me pasan un path, busco en el directorio actual o base
        if path is None:
            path = Path.cwd()

        # traer el path al cliente de la configuracion
        client_path = OeConfig().get_client_path(self._name)
        # No esta en la configuración, verificar si me lo pasan como repositorio
        if not client_path:
            if isinstance(self._args.install, str):
                manifest = self.get_manifest_from_url()
                if manifest:
                    return manifest

        else:
            manifest, _ = self.get_manifest_from_struct(Path(client_path))
            if manifest:
                return manifest

        # no lo encuentro, busco en toda la estructura de directorios
        manifest, path = self.get_manifest_from_struct(path)
        if manifest:
            # si lo encuentro lo guardo en el archivo para la proxima
            OeConfig().save_client_path(self._name, path)
        # devuelvo el manifiesto o None si no esta
        return manifest if manifest else None

    @staticmethod
    def load_manifest(filename: "str | Path") -> dict[str, object]:
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
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            )

            # Convertir a dict seguro
            return ast.literal_eval(text)

        except (OSError, ValueError, SyntaxError):
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

    def get_image_required(self, value):
        """Como get_image pero aborta si la imagen no existe en el proyecto."""
        image = self.get_image(value)
        if not image:
            msg.err(f"There is no '{value}' image on this project")
        return image

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
        return f"{OeConfig().base_dir}odoo-{self._version}{lic}/"

    @property
    def server_version_dir(self):
        """/odoo_ar/odoo-13.0/
        /odoo_ar/odoo-13.0e/
        Esta funcion no tiene que tomar OeConfig().base_dir porque en el servidor es siempre
        /odoo_ar/
        """
        lic = "e" if self._license == "EE" else ""
        return f"/odoo_ar/odoo-{self._version}{lic}/"

    @property
    def base_dir(self):
        """
        Ejemplo: /odoo_ar/odoo-18.0/clientname/

        """
        return f"{self.version_dir}{self._name}/"

    @property
    def server_base_dir(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/"""
        return f"{self.server_version_dir}{self._name}/"

    @property
    def backup_dir(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/backup_dir/"""
        return self.base_dir + "backup_dir/"

    @property
    def server_backup_dir(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/backup_dir/"""
        return f"{self.server_base_dir}backup_dir/"

    @property
    def sources_dir(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/sources/"""
        return self.base_dir + "sources/"

    @property
    def psql_dir(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/postgresql/"""
        return self.base_dir + "postgresql/"

    @property
    def config_file(self):
        """Ejemplo: /odoo_ar/odoo-13.0/clientname/config/odoo.conf"""
        return self.base_dir + "config/odoo.conf"

    @property
    def debug(self):
        # Sigue el environment PERSISTIDO (oe_config.yaml), no el flag
        # transitorio --debug. --debug solo persiste environment=debug; una
        # vez seteado, comandos como `oe -w` (sin --debug) deben seguir en
        # modo debug. Consistente con OdooEnv.debug y con el resto de esta
        # clase (lineas que ya usan OeConfig().debug).
        return OeConfig().debug

    @property
    def prod_server(self):
        return self._prod_server

    @property
    def database_default_name(self):
        return f"{self.name}_prod"
