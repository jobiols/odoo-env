import atexit
import json
import os
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from odoo_env.__init__ import __version__
from odoo_env.messages import msg
from odoo_env.singleton import SingletonMeta


class OeConfig(metaclass=SingletonMeta):

    def __init__(self, args=None):
        # en esta variable guardo toda la data del archivo oe_config.yaml.
        # args es opcional: por ser singleton, __init__ solo corre en la primera
        # construccion (con args reales); las llamadas posteriores OeConfig()
        # devuelven la instancia cacheada sin re-ejecutar __init__.
        # args es un argparse.Namespace (atributos dinamicos) -> Any.
        self._args: Any = args
        self._config_data: dict[str, Any] = self._get_config_data()

    def persist_config(self):
        """Salva en la configuracion los parametros que se declararon como persistentes"""

        if self._args.debug:
            self.save_environment("debug")

        if self._args.prod:
            self.save_environment("prod")

        if self._args.client:
            self.save_client(self._args.client)

        if self._args.base_dir:
            self.save_base_dir(self._args.base_dir)

        if getattr(self._args, "org", None):
            self.save_organization(self._args.org)

    @property
    def client(self):
        """Traer el nombre del cliente"""
        return self.get_client()

    @property
    def config_data(self):
        return self._config_data

    @property
    def base_dir(self):
        return self._config_data.get("base_dir", "/odoo_ar/")

    @property
    def organization(self):
        return self.get_organization()

    @property
    def debug(self):
        return self._config_data.get("environment") == "debug"

    @property
    def prod(self):
        return self._config_data.get("environment") == "prod"

    @staticmethod
    def _user_config_path():
        """Path al archivo de configuración del usuario"""
        return f"{os.path.expanduser('~')}/.config/oe/"

    def _user_config_file(self):
        """Archivo de configuración del usuario"""
        return f"{self._user_config_path()}oe_config.yaml"

    def _get_config_data(self) -> dict[str, Any]:
        """Trae todo el oe_config.yaml como un diccionario"""
        template: dict[str, Any] = {"clients": []}

        try:
            with open(self._user_config_file(), encoding="utf-8") as config:
                data = yaml.safe_load(config)
        except FileNotFoundError:
            return template
        except yaml.YAMLError as e:
            msg.err(f"Invalid YAML in {self._user_config_file()}: {e}")

        # Si está vacío, safe_load devuelve None
        return data or template

    def _save_config_data(self):
        """Salvar el conjunto de paths a los clientes"""
        # En instalacion fresca ~/.config/oe/ no existe todavia; makedirs y open
        # pueden fallar (permisos, disco lleno). Convertimos el OSError crudo en
        # un msg.err claro, igual que _get_config_data hace en la lectura.
        try:
            # chequear si esta el archivo y sino crear el path
            if not os.path.exists(self._user_config_path()):
                os.makedirs(self._user_config_path())

            with open(self._user_config_file(), "w", encoding="utf-8") as config_file:
                yaml.dump(
                    self._config_data,
                    config_file,
                    default_flow_style=False,
                    allow_unicode=True,
                )
        except OSError as e:
            msg.err(f"Could not write config file {self._user_config_file()}: {e}")

    def get_client_path(self, client_name):
        """Traer el path de un cliente desde la config; None si no esta."""

        # Traer la lista de clientes del archivo de configuracion
        clients = self._config_data.get("clients", [])

        path = next((d[client_name] for d in clients if client_name in d), None)
        return Path(path) if path else None

    def save_client_path(self, client_name, path):
        """Salvar el path al cliente solo si no esta, sino no hago nada"""

        if self.get_client_path(client_name):
            return

        # obtengo lista de clientes
        client_list = self._config_data.setdefault("clients", [])
        # agrego el cliente
        client_list.append({client_name: path})
        # salvo la configuracion
        self._save_config_data()

    def get_client(self):
        client_name = self._config_data.get("client")
        if client_name is None:
            msg.err("No default client set. Please specify a client using -c.")
        if not isinstance(client_name, str):
            msg.err("Invalid client name in configuration. must be a string.")
        client_name = client_name.strip().lower()
        if " " in client_name or "/" in client_name:
            msg.err("Invalid client name in configuration. must be a simple name.")
        return client_name

    def save_client(self, client):
        if self._config_data.get("client") == client:
            return

        self._config_data["client"] = client
        self._save_config_data()

    def save_environment(self, environment):
        """Salvar el ambiente"""
        if self._config_data.get("environment") == environment:
            return

        self._config_data["environment"] = environment
        self._save_config_data()

    def get_organization(self):
        """Traer la organizacion de GitHub usada para armar las URLs canonicas.

        Si la clave no esta en el config, persiste y devuelve el default
        'quilsoft-org'.
        """
        org = self._config_data.get("organization")
        if org:
            return org
        self._config_data["organization"] = "quilsoft-org"
        self._save_config_data()
        return "quilsoft-org"

    def save_organization(self, value):
        """Salvar la organizacion (no-op si no cambia)."""
        if self._config_data.get("organization") == value:
            return

        self._config_data["organization"] = value
        self._save_config_data()

    def save_base_dir(self, value):
        """Salvar el base dir"""
        # Asegurar que termina con /
        value = os.path.join(value, "")
        if self._config_data.get("base_dir") == value:
            return

        self._config_data["base_dir"] = value
        self._save_config_data()

    def get_environment(self):
        """Traer el ambiente con prod por defecto"""
        return self._config_data.get("environment", "prod")

    def check_version(self):
        """Chequea si la version de odoo-env es la última y si no avisa al usuario"""

        dt_today = datetime.today()

        last_check = self._config_data.get("last_version_check")
        if last_check is None:
            self._config_data["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self._save_config_data()
            return

        dt_last = datetime.strptime(last_check, "%Y-%m-%d")

        if abs((dt_today - dt_last).days) > 1:
            self._config_data["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self._save_config_data()
            thread = threading.Thread(target=self._fetch_pypi_version, daemon=True)
            thread.start()
            atexit.register(thread.join, 5)

    def _fetch_pypi_version(self):
        try:
            # nosec B310 - URL es un literal https:// constante, sin input
            # externo; no hay forma de inyectar file:// u otro esquema.
            with urllib.request.urlopen(  # nosec B310
                "https://pypi.python.org/pypi/odoo-env/json", timeout=5
            ) as response:
                info = json.loads(response.read().decode("utf-8"))
            version = info["info"]["version"]
            pypi_tuple = tuple(int(x) for x in version.split("."))
            local_tuple = tuple(int(x) for x in __version__.split("."))
            if pypi_tuple > local_tuple:
                msg.warn(
                    f"BE CAREFUL, you are using version {__version__} of odoo-env "
                    f"however version {version} is already available."
                )
                msg.warn(
                    'You should update using "pipx upgrade odoo-env" or "pip '
                    'install --upgrade odoo-env" (old style).\n'
                )
                msg.warn(
                    "Do it right now before chaos knocks your digital door. Dont risk it."
                )
        except (OSError, ValueError, KeyError):
            # OSError cubre urllib.error.URLError; ValueError cubre
            # json.JSONDecodeError. El chequeo de version es best-effort.
            pass
