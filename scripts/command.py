# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from messages import Msg
import subprocess

msg = Msg()


class Command(object):
    def __init__(self,
                 command=False,
                 usr_msg=False,
                 args=False,
                 chck=False,
                 env=False):
        """

        :param command:
        :param usr_msg:
        :param args:
        :param chck:
        :param env:
        :return:
        """
        self._command = command
        self._usr_msg = usr_msg
        self._args = args
        self._chck = chck
        self._env = env
        # el env es requerido
        assert self._env, True

    @property
    def args(self):
        return self._args

    @property
    def usr_msg(self):
        return self._usr_msg

    @property
    def command(self):
        return self._command

    @property
    def command_args(self):
        return self._env._args

    @staticmethod
    def check_path(path):
        return not os.path.isdir(path) if path else False

    def check(self):
        if self._chck == 'path.isdir':
            path = self._args
            return self.check_path(path)

    def execute(self):
        if self.command:
            self.subrpocess_call(self.command.format(self.args))

        return False

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
            if self.command_args.verbose:
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


