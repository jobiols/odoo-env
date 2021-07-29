import os, stat
import subprocess
from odoo_env.__init__ import __version__
from odoo_env.messages import Msg
from odoo_env.odoo_conf import OdooConf

msg = Msg()


class Command:
    def __init__(self, parent, command=False, usr_msg=False, args=False,
                 client_name=False):
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

    def subrpocess_call(self, params, shell=False):
        """ Run command or command list with arguments.  Wait for commands to
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
                msg.run(' ')
                if shell:
                    msg.run(cmd)
                else:
                    msg.run(' '.join(cmd))
                msg.run(' ')
            ret = subprocess.call(cmd, shell=shell)
            if ret:
                return msg.err('The command {} returned with {}'.format(
                    cmd,
                    str(ret)))

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
        values = ['.idea/\n', '*.pyc\n', '__pycache__\n']
        with open(self._command, 'w') as _f:
            for value in values:
                _f.write(value)

    @staticmethod
    def check_args():
        return True

class MakedirCommand(Command):
    def check_args(self):
        # si el directorio existe no lo creamos
        return not os.path.isdir(self._args)

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
        with open('/usr/local/nginx.conf', 'r') as _f:
            conf = _f.read()

        # poner el nombre del cliente en el config
        conf = conf.replace('$client$', self._client_name)

        with open(self._command, 'w') as _f:
            _f.write(conf)


class WriteConfigFile(Command):
    def check_args(self):
        return True

    def execute(self):
        # obtener el cliente a partir del nombre
        arg = self._args
        client = arg['client']

        # obtener los repositorios que hay en sources, para eso se recorre souces y se
        # obtienen todos los directorios que tienen un .git adentro.
        repos = list()
        sources = client.sources_dir
        for root, dirs, _ in os.walk(sources):
            if '.git' in dirs:
                repos.append(root.replace(sources,''))

        repos = ['/opt/odoo/custom-addons/' + x for x in repos]
        repos = ','.join(repos)

        # obtener la configuracion definida en el manifiesto
        conf = client.config or []

        # pisar el config con las cosas agregadas o modificadas, esto permite mantener
        # por ejemplo la contraseña
        odoo_conf = OdooConf(client.config_file)
        odoo_conf.read_config()
        odoo_conf.add_list_data(conf)

        # siempre sobreescribimos estas tres cosas.
        odoo_conf.add_line('addons_path = %s' % repos)
        odoo_conf.add_line('unaccent = True')
        odoo_conf.add_line('data_dir = /opt/odoo/data')

        # si estoy en modo debug, sobreescribo esto
        if client.debug:
            odoo_conf.add_line('workers = 0')
            odoo_conf.add_line('max_cron_threads = 0')
            odoo_conf.add_line('limit_time_cpu = 0')
            odoo_conf.add_line('limit_time_real = 0')
        else:
            # You should use 2 worker threads + 1 cron thread per available CPU
            if 'workers' not in odoo_conf.config:
                odoo_conf.add_line('workers = %s' % (os.cpu_count() * 2))
            if 'max_cron_threads' not in odoo_conf.config:
                odoo_conf.add_line('max_cron_threads = %s' % os.cpu_count())

        odoo_conf.write_config()

        # Corregir los permisos de odoo.conf
        os.chmod(client.config_file, stat.S_IREAD + stat.S_IWRITE + stat.S_IWOTH + stat.S_IROTH)


class MessageOnly(Command):
    @staticmethod
    def check_args():
        """ Siempre lo dejamos pasar
        """
        return True

    @staticmethod
    def execute():
        pass
