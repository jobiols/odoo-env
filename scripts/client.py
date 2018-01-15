# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from messages import Msg
from constants import BASE_DIR
from repos import Repo
from images import Image

msg = Msg()


class Client(object):
    def __init__(self, parent, name):
        """ Busca el cliente en la estructura de directorios, pero si no lo
            encuentra pide un directorio donde esta el repo que contiene al
        """
        self._parent = parent
        self._name = name

        # si estamos en test accedo a data
        if name[0:5] == 'test_':
            path = os.path.dirname(os.path.abspath(__file__))
            manifest = self.get_manifest(path + '/../data')
        else:
            manifest = self.get_manifest(BASE_DIR)
        if not manifest:
            msg.inf('Can not find client {} in this host. Please provide path '
                    'to repo\n where it is or hit Enter to exit.'
                    '\n'.format(self._name))

            # path = raw_input('path = ')
            path = '/home/jobiols/kk'
            manifest = self.get_manifest(path)
            if not manifest:
                msg.err('Can not find client {} in this host'.format(name))

            msg.inf('Client found!')
            msg.inf('Name {}\nversion {}\n'.format(manifest.get('name'),
                                                   manifest.get('version')))

        # Chequar que este todo bien
        if not manifest.get('images'):
            msg.err('No images in manifest {}'.format(self.name))

        if not manifest.get('repos'):
            msg.err('No repos in manifest {}'.format(self.name))

        self._port = manifest.get('port')
        if not self._port:
            msg.err('No port in manifest {}'.format(self.name))

        self._version = manifest.get('version')[0:3]
        if not self._version:
            msg.err('No version tag in manifest {}'.format(self.name))

        # Crear imagenes y repos
        self._repos = []
        for rep in manifest.get('repos'):
            self._repos.append(Repo(rep))

        self._images = []
        for img in manifest.get('images'):
            self._images.append(Image(img))

        if not self._name == manifest.get('name').lower():
            msg.err('You intend to install client {} but in manifest name '
                    'then name is {}'.format(self._name,
                                             manifest.get('name')))

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
                    if manifest.get('name').lower() == self._name:
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

    def image(self, image_name):
        for img_dict in self._images:
            if img_dict['name'] == image_name:
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
        msg.err('No image {} found'.format(value))


    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def numeric_ver(self):
        return int(self.version)

    @property
    def base_dir(self):
        return '{}odoo-{}/{}/'.format(BASE_DIR, self._version, self._name)

    @property
    def repos(self):
        return self._repos

    @property
    def images(self):
        return self._images

    @property
    def sources_dir(self):
        return self.base_dir + 'sources/'

    @property
    def psql_dir(self):
        return self.base_dir + 'postgresql/'

    @property
    def port(self):
        return self._port
