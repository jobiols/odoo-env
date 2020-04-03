# -*- coding: utf-8 -*-

import os
import ast
from odoo_env.messages import Msg
from odoo_env.constants import BASE_DIR
from odoo_env.repos import Repo, Repo2
from odoo_env.images import Image, Image2
from odoo_env.config import OeConfig

msg = Msg()


class Client(object):
    def __init__(self, odooenv, name):
        """ Busca el cliente en la estructura de directorios, pero si no lo
            encuentra pide un directorio donde esta el repo que lo contiene
        """
        # parent es siempre un objeto OdooEnv
        self._parent = odooenv
        self._name = name
        self._license = False
        self._images = []
        self._repos = []
        self._port = 0
        self._version = ''
        self.CPUs = 1
        self.limit_request = '0'
        self.limit_memory_soft = '0'
        self.limit_memory_hard = '0'
        self.limit_time_cpu = '0'
        self.limit_time_real = '0'

        # si estamos en test accedo a data
        if name[0:5] in ['test_', 'test2']:
            path = os.path.dirname(os.path.abspath(__file__))
            path = path.replace('odoo_env', 'odoo_env/data')
            manifest = self.get_manifest(path)
            OeConfig().save_client_path(name, path)
        else:
            manifest = self.get_manifest(BASE_DIR)
        if not manifest:
            msg.inf('Can not find client {} in this host installation.\n'
                    'We will try in current dir'.format(self._name))

            # mantener compatibilidad con python2
            import six
            six.moves.input('Hit Enter to continue or CTRL C to exit')
            manifest, _ = self.get_manifest_from_struct(os.getcwd())
            if not manifest:
                msg.err('Can not find client {} in current dir'.format(name))

            msg.inf('Client found!')
            msg.inf('Name {}\nversion {}\n'.format(manifest.get('name'),
                                                   manifest.get('version')))

        self.check_common(manifest)

        # verificar version del manifiesto
        ver = manifest.get('env-ver', '1')
        if ver == '1':
            self.check_v1(manifest)
        elif ver == '2':
            self.check_v2(manifest)
        else:
            msg.err('not supported syntax version in manifest')

    def check_v1(self, manifest):
        # Chequar que el manifiesto tenga bien las cosas
        if not manifest.get('docker'):
            msg.err('No images in manifest {}'.format(self.name))

        if not manifest.get('repos'):
            msg.err('No repos in manifest {}'.format(self.name))

        # Crear imagenes y repos
        self._repos = []
        for rep in manifest.get('repos'):
            self._repos.append(Repo(rep))

        self._images = []
        for img in manifest.get('docker'):
            self._images.append(Image(img))

    def check_v2(self, manifest):
        # Chequar que el manifiesto tenga bien las cosas
        if not manifest.get('docker-images'):
            msg.err('No images in manifest %s' % self.name)

        if not manifest.get('git-repos'):
            msg.err('No repos in manifest %s' % self.name)

        # leer si es enterprise o community
        self._license = manifest.get('license', False)

        if not self._license:
            msg.err('No license, in manifest %s' % self.name)

        if self._license not in ['EE', 'CE']:
            msg.err('license must be EE or CE')

        # Crear imagenes y repos
        for rep in manifest.get('git-repos'):
            self._repos.append(Repo2(rep, self._version))

        for img in manifest.get('docker-images'):
            self._images.append(Image2(img))

    def check_common(self, manifest):
        self._port = manifest.get('port')
        if not self._port:
            msg.err('No port in manifest {}'.format(self.name))

        ver = manifest.get('version')
        if not ver:
            msg.err('No version tag in manifest {}'.format(self.name))
        x = ver.find('.') + 1
        y = ver[x:].find('.') + x
        self._version = ver[0:y]

        # get first word of name in lowercase
        name = manifest.get('name').lower()
        if not self._name == name.split()[0]:
            msg.err('You intend to install client %s but in manifest, '
                    'the name is %s' % (self._name, manifest.get('name')))

        # Tomar los datos de instalacion.

        cpus = manifest.get('CPUs', False)
        import multiprocessing as mp
        # si me definieron las cpu uso eso sino verifico cuantas hay
        self.CPUs = int(cpus) if cpus else mp.cpu_count()
        self.limit_request = manifest.get('limit_request', 8196)
        self.limit_memory_soft = manifest.get('limit_memory_soft', 640000000)
        self.limit_memory_hard = manifest.get('limit_memory_hard', 760000000)
        self.limit_time_cpu = manifest.get('limit_time_cpu', 60)
        self.limit_time_real = manifest.get('limit_time_real', 120)

    def get_manifest_from_struct(self, path):
        """ leer un manifest que esta dentro de una estructura de directorios
            revisar toda la estructura hasta encontrar un manifest.
            devolver el manifest y el path
        """
        for root, dirs, files in os.walk(path):
            for file in ['__openerp__.py',
                         '__manifest__.py',
                         '__manifest_tst_.py']:
                if file in files:
                    manifest_file = '%s/%s' % (root, file)
                    manifest = self.load_manifest(manifest_file)

                    # get first word of name in lowercase
                    name = manifest.get('name').lower()
                    # por si viene sin name
                    if name:
                        name = name.split()[0]
                        if name == self._name:
                            return manifest, root
        return False, False

    def get_manifest(self, path):
        """
        :param path: path base para buscar el cliente
        :return: manifiesto del cliente
        """
        # traer el path al cliente de la configuracion
        client_path = OeConfig().get_client_path(self._name)
        # si lo encuentro traigo el manifest rapidamente con el path
        if client_path:
            manifest, _ = self.get_manifest_from_struct(client_path)
            return manifest
        else:
            # no lo encuentro, busco en toda la estructura de directorios
            manifest, path = self.get_manifest_from_struct(path)
            if manifest:
                # si lo encuentro lo guardo en el archivo para la proxima
                OeConfig().save_client_path(self._name, path)
            # devuelvo el manifiesto o false si no esta
            return manifest

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
                ret = ast.literal_eval(manifest)
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
    def version_dir(self):
        """ /odoo_ar/odoo-13.0/
            /odoo_ar/odoo-13.0e/
        """
        lic = 'e' if self._license == 'EE' else ''
        return '%sodoo-%s%s/' % (BASE_DIR, self._version, lic)

    @property
    def base_dir(self):
        """ /odoo_ar/odoo-13.0/clientname/
            /odoo_ar/odoo-13.0e/clientname/
        """
        return '%s%s/' % (self.version_dir, self._name)

    @property
    def backup_dir(self):
        """ /odoo_ar/odoo-13.0/clientname/backup_dir/
        """
        return self.base_dir + 'backup_dir/'

    @property
    def sources_dir(self):
        """ /odoo_ar/odoo-13.0/clientname/sources/
        """
        return self.base_dir + 'sources/'

    @property
    def psql_dir(self):
        """ /odoo_ar/odoo-13.0/clientname/postgresql/
        """
        return self.base_dir + 'postgresql/'

    @property
    def config_file(self):
        """ /odoo_ar/odoo-13.0/clientname/config/odoo.conf
        """
        return self.base_dir + 'config/odoo.conf'

    @property
    def nginx_dir(self):
        """ /odoo_ar/nginx/
        """
        return '%snginx/' % BASE_DIR
