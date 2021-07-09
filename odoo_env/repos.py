# -*- coding: utf-8 -*-


class Repo(object):
    def __init__(self, value):
        self._dict = value

    @property
    def name(self):
        return self._dict.get('repo')

    @property
    def dir_name(self):
        return self._dict.get('repo')

    @property
    def branch(self):
        return self._dict.get('branch')

    @property
    def url(self):
        if self._dict.get('ssh', False):
            template = 'git@{}:{}/{}'
        else:
            template = 'https://{}/{}/{}'

        return template.format(self._dict.get('host', 'github.com'),
                               self._dict.get('usr'),
                               self._dict.get('repo'))

    @property
    def formatted(self):
        aaa = self._dict['usr'] + '/' + self._dict['repo']
        ret = 'b ' + self._dict['branch'].ljust(7) + ' ' + aaa.ljust(30)
        return ret

    @property
    def clone(self):
        return 'clone --depth 1 -b {} {}'.format(self.branch, self.url)

    @property
    def pull(self):
        return 'pull'


class Repo2(object):
    def __init__(self, value, branch):
        """ Sintaxis <repo> [<directory>[/<directory>] [-b <branch>]
            El branch debe estar despues del repo, si no esta se toma el branch
            que viene como parametro, si no viene nada es una excepcion.
            El directorio va despues del repo y puede no estar
        """
        # parsear value en una lista
        parsed = value.split(' ')
        # eliminar los espacios
        parsed = [i for i in parsed if i != '']
        # obtener el branch si es que existe
        if '-b' in parsed:
            index = parsed.index('-b')
            self._branch = parsed[index + 1]
            # eliminar el -b y el parametro branch
            parsed.remove('-b')
            parsed.remove(self._branch)
        else:
            self._branch = branch

        self._url = parsed[0]

        # si me quedan dos parametros tengo un directorio
        if len(parsed) > 1:
            self._dir = parsed[1]
            self._extra_dir = True
        else:
            parsed = self._url.split('/')
            self._dir = parsed[len(parsed) -1].replace('.git', '')
            self._extra_dir = False

    @property
    def dir_name(self):
        """ Obtener el directorio donde se pone el repo
        """
        return self._dir

    @property
    def branch(self):
        return self._branch

    @property
    def url(self):
        if self._extra_dir:
            return '%s %s' % (self._url, self._dir)
        else:
            return self._url

    @property
    def formatted(self):
        if self._extra_dir:
            return 'b %s     %s >> %s' % (self.branch, self._url, self._dir)
        else:
            return 'b %s     %s' % (self.branch, self.url)


    @property
    def clone(self):
        return 'clone --depth 1 -b %s %s' % (self.branch, self.url)

    @property
    def pull(self):
        return 'pull'
