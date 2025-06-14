import json
import os
from datetime import datetime

import tornado
import tornado.httpclient
import tornado.options
import tornado.process
import tornado.web
import tornado.websocket
import yaml

from odoo_env.__init__ import __version__
from odoo_env.messages import Msg

USER_CONFIG_PATH = os.path.expanduser("~") + "/.config/oe/"
USER_CONFIG_FILE = USER_CONFIG_PATH + "oe_config.yaml"
USER_CONFIG_FILE_TEST = USER_CONFIG_PATH + "oe_config_test.yaml"

oe_config = False

_instances = {}


class Singleton:
    def __new__(cls, *args, **kw):
        if cls not in _instances:
            instance = super().__new__(cls)
            _instances[cls] = instance
        return _instances[cls]


class OeConfig(Singleton):
    @staticmethod
    def get_config_data():
        template = {"clients": []}
        # obtener el archivo con los datos de clientes
        try:
            with open(USER_CONFIG_FILE) as config:
                ret = yaml.safe_load(config)
        except Exception:
            return template
        return ret if ret else template

    def save_config_data(self, config):
        """ Salvar el conjunto de paths a los clientes
        """ ""
        # chequear si esta el archivo y sino crear el path
        if not os.path.exists(USER_CONFIG_PATH):
            os.makedirs(USER_CONFIG_PATH)

        with open(USER_CONFIG_FILE, "w") as config_file:
            yaml.dump(config, config_file, default_flow_style=False, allow_unicode=True)

    def get_base_dir(self):
        config = self.get_config_data()
        return config.get("base_dir", "/odoo_ar/")

    def get_client_path(self, client_name):
        """Traer el path de un cliente"""
        config = self.get_config_data()

        clients = config.get("clients", False)

        for client in clients:
            if client.get(client_name):
                return client.get(client_name)
        return False

    def save_client_path(self, client_name, path):
        """Salvar el path al cliente, una sola vez"""
        if not self.get_client_path(client_name):
            # me traigo la configuracion
            config = self.get_config_data()
            # obtengo lista de clientes
            client_list = config["clients"]
            # agrego el cliente
            client_list.append({client_name: path})
            # salvo la configuracion
            self.save_config_data(config)

    def get_client(self):
        config = self.get_config_data()
        return config.get("client", False)

    def save_client(self, client):
        config = self.get_config_data()
        config["client"] = client
        self.save_config_data(config)

    def get_environment(self):
        """Traer el ambiente con prod por defecto"""
        config = self.get_config_data()
        return config.get("environment", "prod")

    def save_environment(self, environment):
        """Salvar el ambiente"""
        config = self.get_config_data()
        config["environment"] = environment
        self.save_config_data(config)

    def save_base_dir(self, value):
        """Salvar el base dir"""
        config = self.get_config_data()
        # Asegurar que termina con /
        value = os.path.join(value, "")
        config["base_dir"] = value
        self.save_config_data(config)

    def check_version(self):
        """Chequea si la version de odoo-env es la última"""

        config = self.get_config_data()
        dt_today = datetime.today()

        # veo las fechas, si no tiene fecha es que esta recien instalado
        # me guardo la fecha y termino
        last_check = config.get("last_version_check", False)
        if not last_check:
            config["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self.save_config_data(config)
            return True

        # tiene fecha, la paso a datetime
        dt_last = datetime.strptime(last_check, "%Y-%m-%d")

        # verifico la version cada 10 dias
        if abs((dt_today - dt_last).days) > 10:
            # guardo la fecha del chequeo
            config["last_version_check"] = dt_today.strftime("%Y-%m-%d")
            self.save_config_data(config)

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
                    Msg().warn(
                        f"BE CAREFUL, you are using version {__version__} of odoo-env "
                        f"however version {version} is already available."
                    )
                    Msg().warn(
                        'You should update using "pipx upgrade odoo-env" or "pip '
                        'install --upgrade odoo-env" (old style).\n'
                    )
                    Msg().warn(
                        "Do it right now before chaos knocks your digital door. Dont risk it."
                    )

            except Exception:
                Msg().inf(
                    "Oops! It seems my cowboy hat ran out of internet connection. "
                    "Did you feed coins to the internet ranch, or did the Wi-Fi birds "
                    "fly away?"
                )

        return True
