import json
import os
from datetime import datetime
from pathlib import Path

import tornado
import tornado.httpclient
import yaml

from odoo_env.__init__ import __version__
from odoo_env.messages import msg
from odoo_env.singleton import SingletonMeta

class OeConfig(metaclass=SingletonMeta):

    def __init__(self, args):
        # en esta variable guardo toda la data del archivo oe_config.yaml
        self._args = args
        self._config_data = self._get_config_data()
        print(f"Inicializando OeConfig: -------------------------------------------------- ")

    def persist_config(self):
        """Salva en la configuracion los parametros que se declararon como persistentes"""

        if self._args.debug:
            self.save_environment("debug")

        if self._args.prod:
            self.save_environment("prod")

        if self._args.client:
            self.save_client(self.client)

        if self._args.base_dir:
            self.save_base_dir(self.base_dir)

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

    def _get_config_data(self):
        """Trae todo el oe_config.yaml como un diccionario"""
        template = {"clients": []}

        try:
            with open(self._user_config_file()) as config:
                data = yaml.safe_load(config)
        except FileNotFoundError:
            return template
        except yaml.YAMLError as e:
            msg.err(f"Invalid YAML in {self._user_config_file()}: {e}")
            return template

        # Si está vacío, safe_load devuelve None
        return data or template

    def _save_config_data(self):
        """Salvar el conjunto de paths a los clientes"""
        # chequear si esta el archivo y sino crear el path
        if not os.path.exists(self._user_config_path()):
            os.makedirs(self._user_config_path())

        with open(self._user_config_file(), "w") as config_file:
            yaml.dump(
                self._config_data,
                config_file,
                default_flow_style=False,
                allow_unicode=True,
            )

    def get_client_path(self, client_name):
        """Traer el path de un cliente desde el archivo de configuracion, si no esta devuelve None"""

        # Traer la lista de clientes del archivo de configuracion
        clients = self._config_data.get("clients")

        path = next((d[client_name] for d in clients if client_name in d), None)
        return Path(path) if path else None

    def save_client_path(self, client_name, path):
        """Salvar el path al cliente solo si no esta, sino no hago nada"""

        if self.get_client_path(client_name):
            return

        # obtengo lista de clientes
        client_list = self._config_data.get("clients")
        # agrego el cliente
        client_list.append({client_name: path})
        # salvo la configuracion
        self._save_config_data()

    def get_client(self):
        client_name = self._config_data.get("client")
        if client_name is None:
            msg.err("No default client set. Please specify a client using --client.")
        if not isinstance(client_name, str):
            msg.err("Invalid client name in configuration. must be a string.")
        client_name = client_name.strip().lower()
        if " " in client_name or "/" in client_name:
            msg.err("Invalid client name in configuration. must be a simple name.")
        return client_name

    def save_client(self, client):
        if self._config_data["client"] == client:
            return

        self._config_data["client"] = client
        self._save_config_data()

    def save_environment(self, environment):
        """Salvar el ambiente"""
        if self._config_data["environment"] == environment:
            return

        self._config_data["environment"] = environment
        self._save_config_data()

    def save_base_dir(self, value):
        """Salvar el base dir"""
        # Asegurar que termina con /
        value = os.path.join(value, "")
        if self._config_data["base_dir"] == value:
            return

        self._config_data["base_dir"] = value
        self._save_config_data()

    def get_environment(self):
        """Traer el ambiente con prod por defecto"""
        return self._config_data.get("environment", "prod")

    def check_version(self):
        """Chequea si la version de odoo-env es la última y si no avisa al usuario"""

        dt_today = datetime.today()

        # veo las fechas, si no tiene fecha es que esta recien instalado
        # me guardo la fecha y termino
        last_check = self._config_data.get("last_version_check")
        if last_check is None:
            self._config_data["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self._save_config_data()

        # tiene fecha, la paso a datetime
        dt_last = datetime.strptime(last_check, "%Y-%m-%d")

        # verifico la version cada 10 dias
        if abs((dt_today - dt_last).days) > 1:
            # guardo la fecha del chequeo
            self._config_data["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self._save_config_data()

            http = tornado.httpclient.HTTPClient()
            try:
                response = http.fetch(
                    "https://pypi.python.org/pypi/odoo-env/json",
                    connect_timeout=5,
                    request_timeout=5,
                )
                info = json.loads(response.buffer.read().decode("utf-8"))
                version = info["info"]["version"]
                if version != __version__:
                    msg().warn(
                        f"BE CAREFUL, you are using version {__version__} of odoo-env "
                        f"however version {version} is already available."
                    )
                    msg().warn(
                        'You should update using "pipx upgrade odoo-env" or "pip '
                        'install --upgrade odoo-env" (old style).\n'
                    )
                    msg().warn(
                        "Do it right now before chaos knocks your digital door. Dont risk it."
                    )

            except Exception:
                msg().inf(
                    "Oops! Looks like my cowboy hat is out of internet. "
                    "Did you forget to feed coins to the internet ranch, or did the Wi-Fi birds "
                    "fly away again?"
                )
