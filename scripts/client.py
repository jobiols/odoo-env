# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from messages import Msg
from constants import BASE_DIR

msg = Msg()


class Client(object):
    def __init__(self, name):
        """ Busca el cliente en la estructura de directorios, pero si no lo
            encuentra pide un directorio donde esta el repo que contiene al
            cliente.
        """
        for root, dirs, files in os.walk(BASE_DIR):
            for file in ['__openerp__.py', '__odoo__.py']:
                if file in files:
                    manifest_file = '{}/{}'.format(root, file)
                    manifest = self.load_manifest(manifest_file)
                    if manifest:
                        break

        self._images = manifest.get('images')
        self._repos = manifest.get('repos')
        self._version = manifest.get('version')[0:3]
        self._name = name

        if not self._images:
            msg.err('No images in manifest {}'.format(manifest_file))

        if not self._repos:
            msg.err('No repos in manifest {}'.format(manifest_file))

        if not self._version:
            msg.err('No version tag in manifest {}'.format(manifest_file))

    @staticmethod
    def load_manifest(filename):
        """ se le pasa el manifiesto del cliente y de ahi levanta los datos
            para armar el objeto y los devuelve
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
