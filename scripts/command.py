# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from messages import Msg
import subprocess

msg = Msg()


class Command(object):
    def __init__(self, parent, command=False, usr_msg=False, args=False):
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

    def check(self):
        # si no tiene argumentos para chequear no requiere chequeo,
        # lo dejamos pasar
        if not self._args:
            return True

        # le pasamos el chequeo al objeto especifico
        return self.check_args(self.args)

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
    @staticmethod
    def check_args(path):
        # si el directorio existe no lo creamos
        return not os.path.isdir(path)


class ExtractSourcesCommand(Command):
    @staticmethod
    def check_args(path):
        # si el directorio tiene archivos no copiamos los fuentes
        return os.listdir(path) == []

