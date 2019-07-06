# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from __future__ import absolute_import

import os
try:
    from messages import Msg
except ImportError:
    from odoo_env.messages import Msg
import subprocess

msg = Msg()


class Command:
    def __init__(
        self, parent, command=False, usr_msg=False, args=False,
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


class MakedirCommand(Command):
    def check_args(self):
        # si el directorio existe no lo creamos
        return not os.path.isdir(self._args)


class ExtractSourcesCommand(Command):
    def check_args(self):
        # si el directorio tiene archivos no copiamos los fuentes
        return os.listdir(self._args) == []


class CloneRepo(Command):
    def check_args(self):
        # si el directorio no existe dejamos clonar
        return not os.path.isdir(self._args)


class PullRepo(Command):
    def check_args(self):
        # si el directorio existe dejamos pulear
        return os.path.isdir(self._args)


class PullImage(Command):
    def check_args(self):
        return True


class CreateNginxTemplate(Command):
    def check_args(self):
        # si el archivo existe no lo dejamos pasar
        return not os.path.isfile(self._args)

    def execute(self):
        # crear el nginx.conf
        with open('/usr/local/nginx.conf', 'r') as f:
            conf = f.read()

        # poner el nombre del cliente en el config
        conf = conf.replace('$client$', self._client_name)

        with open(self._command, 'w') as f:
            f.write(conf)


class MessageOnly(Command):
    @staticmethod
    def check_args(self):
        """ Siempre lo dejamos pasar
        """
        return True

    @staticmethod
    def execute():
        pass
