# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from messages import Msg
from constants import BASE_DIR

msg = Msg()


class Client(object):
    def __init__(self, env, name):
        """ Busca el cliente en la estructura de directorios, pero si no lo
            encuentra pide un directorio donde esta el repo que contiene al
            cliente.
        """
        self._env = env
        manifest = self.get_manifest(BASE_DIR)
        if not manifest:
            msg.inf('Can not find client {} in this host. Please provide path '
                    'to repo\n where it is or hit Enter to exit.'
                    '\n'.format(name))

            # path = raw_input('path = ')
            path = '/home/jobiols/kk'
            manifest = self.get_manifest(path)
            if not manifest:
                msg.err('Can not find client {} in this host'.format(name))

        self._images = manifest.get('images')
        self._repos = manifest.get('repos')
        self._version = manifest.get('version')[0:3]
        self._name = manifest.get('name').lower()

        if not self._images:
            msg.err('No images in manifest {}'.format(self.name))

        if not self._repos:
            msg.err('No repos in manifest {}'.format(self.name))

        if not self._version:
            msg.err('No version tag in manifest {}'.format(self.name))

    def get_manifest(self, path):
        """
        :param path: base dir to walk searching for manifest
        :return: parsed manifest file as dictionary
        """
        for root, dirs, files in os.walk(path):
            for file in ['__openerp__.py', '__odoo__.py']:
                if file in files:
                    manifest_file = '{}/{}'.format(root, file)
                    manifest = self.load_manifest(manifest_file)
                    if manifest.get('name').lower() == self.env.args.client[0]:
                        return manifest

        return False

    @staticmethod
    def load_manifest(filename):
        """
        Loads a manifest
        :param filename: absolute filename to manifest
        :return: manifest in dictionary format
        """
        manifest = ''
        with open(filename, 'r') as f:
            for line in f:
                if line.strip() and line.strip()[0] != '#':
                    manifest += line
            ret = eval(manifest)
            return ret

    @property
    def sources_dir(self):
        return '/odoo/odoo-8.0/sources'

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def env(self):
        return self._env
