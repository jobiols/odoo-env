# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
try:
    from messages import Msg
    from constants import BASE_DIR
    from repos import Repo
    from images import Image
except ImportError:
    from odoo_env.messages import Msg
    from odoo_env.constants import BASE_DIR
    from odoo_env.repos import Repo
    from odoo_env.images import Image

msg = Msg()


class Client(object):
    def __init__(self, odooenv, name):
        """ Busca el cliente en la estructura de directorios, pero si no lo
            encuentra pide un directorio donde esta el repo que lo contiene
        """
        # parent es siempre un objeto OdooEnv
        self._parent = odooenv
        self._name = name

        # si estamos en test accedo a data
        if name[0:5] == 'test_':
            path = os.path.dirname(os.path.abspath(__file__))
            path = path.replace('odoo_env', 'odoo_env/data')
            manifest = self.get_manifest(path)
        else:
            manifest = self.get_manifest(BASE_DIR)
        if not manifest:
            msg.inf('Can not find client {} in this host. Please provide path '
                    'to repo\n where it is or hit Enter to exit.'
                    '\n'.format(self._name))

            path = raw_input('path = ')
            manifest = self.get_manifest(path)
            if not manifest:
                msg.err('Can not find client {} in this host'.format(name))

            msg.inf('Client found!')
            msg.inf('Name {}\nversion {}\n'.format(manifest.get('name'),
                                                   manifest.get('version')))

        # Chequar que este todo bien
        if not manifest.get('docker'):
            msg.err('No images in manifest {}'.format(self.name))

        if not manifest.get('repos'):
            msg.err('No repos in manifest {}'.format(self.name))

        self._port = manifest.get('port')
        if not self._port:
            msg.err('No port in manifest {}'.format(self.name))

        ver = manifest.get('version')
        if not ver:
            msg.err('No version tag in manifest {}'.format(self.name))
        x = ver.find('.') + 1
        y = ver[x:].find('.') + x
        self._version = ver[0:y]

        # Crear imagenes y repos
        self._repos = []
        for rep in manifest.get('repos'):
            self._repos.append(Repo(rep))

        self._images = []
        for img in manifest.get('docker'):
            self._images.append(Image(img))

        # todo codigo repetido
        # get first word of name in lowercase
        name = manifest.get('name').lower()
        if not self._name == name.split()[0]:
            msg.err('You intend to install client {} but in manifest, '
                    'the name is {}'.format(self._name, manifest.get('name')))

    def get_manifest(self, path):
        """
        :param path: base dir to walk searching for manifest
        :return: parsed manifest file as dictionary
        """
        for root, dirs, files in os.walk(path):
            for file in ['__openerp__.py', '__manifest__.py']:
                if file in files:
                    manifest_file = '{}/{}'.format(root, file)
                    manifest = self.load_manifest(manifest_file)
                    # todo codigo repetido
                    # get first word of name in lowercase
                    name = manifest.get('name').lower()
                    # por si viene sin name
                    if name:
                        name = name.split()[0]
                        if name == self._name:
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
            try:
                ret = eval(manifest)
            except Exception:
                return {'name': 'none'}
            return ret

    def image(self, image_name):
        for img_dict in self._images:
            if img_dict.get('name') == image_name:
                img = img_dict.get('img')
                ver = img_dict.get('ver')
                ret = img_dict.get('usr')
                if img:
                    ret += '/' + img
                if ver:
                    ret += ':' + ver
                return ret
        msg.err('There is no {} image found in this manifest'.format(
            image_name))

    def get_image(self, value):
        for image in self._images:
            if image.short_name == value:
                return image
        return False

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def numeric_ver(self):
        return float(self.version[0:2])

    @property
    def repos(self):
        return self._repos

    @property
    def images(self):
        return self._images

    @property
    def port(self):
        return self._port

    @property
    def psql_dir(self):
        return self.base_dir + 'postgresql/'

    @property
    def base_dir(self):
        return '{}odoo-{}/{}/'.format(BASE_DIR, self._version, self._name)

    @property
    def version_dir(self):
        return '{}odoo-{}/'.format(BASE_DIR, self._version)

    @property
    def sources_dir(self):
        """ links to repos for this client only pointing to sources_com """
        return self.base_dir + 'sources/'

    @property
    def sources_com(self):
        """ real repos for this odoo Version, all clients """
        return '{}odoo-{}/sources/'.format(BASE_DIR, self._version)

    @property
    def nginx_dir(self):
        """ Base dir for nginx """
        return '{}nginx/'.format(BASE_DIR)

    @property
    def backup_dir(self):
        return self.base_dir + 'backup_dir/'
