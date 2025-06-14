import os
import stat
import subprocess
from pathlib import Path

from odoo_env.messages import Msg
from odoo_env.odoo_conf import OdooConf

msg = Msg()


class Command:
    def __init__(
        self, parent, command=False, usr_msg=False, args=False, client_name=False
    ):
        """
        :param parent: El objeto OdooEnv que lo contiene por los parametros
        :param command: El comando a ejecutar en el shell
        :param usr_msg: El mensaje a mostrarle al usuario
        :param args: Argumentos para chequear, define si se ejecuta o no
        :return: El objeto Comando que se ejecutara luego
        """
        self._parent = parent
        self._command = command
        self._usr_msg = usr_msg
        self._args = args
        self._client_name = client_name

    def check(self):
        # si no tiene argumentos para chequear no requiere chequeo,
        # lo dejamos pasar
        if not self._args:
            return True

        # le pasamos el chequeo al objeto especifico
        return self.check_args()

    def check_args(self):
        raise NotImplementedError

    def execute(self):
        cmd = self.command
        self.subrpocess_call(cmd)

    def subrpocess_call(self, params, shell=True):
        """Run command or command list with arguments.  Wait for commands to
            complete
            If args.verbose is true, prints command
            If any errors stop list execution and returns error
            if shell=True go shell mode (only for --cron-jobs)

        :param params: command or command list
        :return: error return
        """
        # if not a list convert to a one element list
        params = params if isinstance(params, list) else [params]

        # traverse list executing shell commands
        for _cmd in params:
            # if shell = True we do no split
            cmd = _cmd if shell else _cmd.split()
            if self._parent.verbose:
                msg.run(" ")
                if shell:
                    msg.run(cmd)
                else:
                    msg.run(" ".join(cmd))
                msg.run(" ")
            ret = subprocess.call(cmd, shell=shell)
            if ret:
                if "hmod o+w" in cmd:
                    return msg.warn(f"The command {cmd} returned with {str(ret)}")
                else:
                    return msg.err(f"The command {cmd} returned with {str(ret)}")

    @property
    def args(self):
        return self._args

    @property
    def usr_msg(self):
        return self._usr_msg

    @property
    def command(self):
        return self._command


class CreateGitignore(Command):
    def execute(self):
        # crear el gitignore en el archivo que viene del comando
        values = [".idea/\n", "*.pyc\n", "__pycache__\n"]
        with open(self._command, "w") as _f:
            for value in values:
                _f.write(value)

    @staticmethod
    def check_args():
        return True


class MakedirCommand(Command):
    def check_args(self):
        # si el directorio existe no lo creamos
        return not os.path.isdir(self._args)


class RemovedirCommand(Command):
    def check_args(self):
        # si el directorio existe lo borramos
        return os.path.isdir(self._args)


class ExtractSourcesCommand(Command):
    @staticmethod
    def check_args():
        return True


class CloneRepo(Command):
    def check_args(self):
        # si el directorio no existe dejamos clonar
        return not os.path.isdir(self._args)


class PullRepo(Command):
    def check_args(self):
        # si el directorio existe dejamos pulear
        return os.path.isdir(self._args)


class PullImage(Command):
    @staticmethod
    def check_args():
        return True


class CreateNginxTemplate(Command):
    def check_args(self):
        # si el archivo existe no lo dejamos pasar
        return not os.path.isfile(self._args)

    def execute(self):
        # leer el nginx.conf
        with open("/usr/local/nginx.conf") as _f:
            conf = _f.read()

        # poner el nombre del cliente en el config
        conf = conf.replace("$client$", self._client_name)

        with open(self._command, "w") as _f:
            _f.write(conf)


class WriteConfigFile(Command):
    def check_args(self):
        return True

    def check_item(self, search_item, search_list):
        for item in search_list:
            if search_item in item:
                return item
        return False

    def execute(self):
        arg = self._args
        client = arg["client"]

        # obtener los repositorios que hay en sources, para eso se recorre souces y se
        # obtienen todos los directorios que tienen un .git adentro.
        repos = []
        base = Path(client.sources_dir)

        manifest_files = list(base.rglob("__manifest__.py"))
        for manifest in manifest_files:
            module_path = str(manifest.parent.parent.relative_to(client.sources_dir))
            if not module_path in repos:
                repos.append(module_path)

        repos = ["/opt/odoo/custom-addons/" + x for x in repos]
        repos = ",".join(repos)

        # Actualizar el archivo odoo.conf

        # Leer el archivo de configuracion original
        odoo_conf = OdooConf(client.config_file)
        odoo_conf.read_config()

        odoo_conf.add_list_data(client.config)

        # siempre sobreescribimos estas tres cosas.
        odoo_conf.add_line("addons_path = %s" % repos)
        odoo_conf.add_line("unaccent = True")
        odoo_conf.add_line("data_dir = /opt/odoo/data")

        # si estoy en modo debug, sobreescribo esto
        if client.debug:
            odoo_conf.add_line("workers = 0")
            odoo_conf.add_line("max_cron_threads = 0")
            odoo_conf.add_line("limit_time_cpu = 0")
            odoo_conf.add_line("limit_time_real = 0")
            odoo_conf.add_line("admin_passwd = admin")
        else:
            # no estoy en modo debug,
            # si no defino workers en el manifiesto lo calculo
            line = self.check_item("workers", client.config)
            if not line:
                # Calculo los workers
                # You should use 2 worker threads per CPU
                odoo_conf.add_line(f"workers = {(os.cpu_count() * 2)}")
            else:
                odoo_conf.add_line(line)

            # si no defino cron_threads en el manifiesto lo calculo
            line = self.check_item("max_cron_threads", client.config)
            if not line:
                # Calculo los cron threads
                odoo_conf.add_line("max_cron_threads = 1")
            else:
                odoo_conf.add_line(line)

        odoo_conf.write_config()

        # Corregir los permisos de odoo.conf
        os.chmod(
            client.config_file,
            stat.S_IREAD + stat.S_IWRITE + stat.S_IWOTH + stat.S_IROTH,
        )


class MessageOnly(Command):
    @staticmethod
    def check_args():
        """Siempre lo dejamos pasar"""
        return True

    @staticmethod
    def execute():
        pass
