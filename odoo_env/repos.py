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
        # chequear branch alternativo
        i = value.find(' -b ')
        if i >= 0:
            branch = value[i+4:]
            value = value[:i]

        self._data = value
        self._branch = branch

    @property
    def name(self):
        return self._dict.get('repo')

    @property
    def dir_name(self):
        """ Obtener el directorio donde se pone el repo
        """
        url = self._data.split()
        if len(url) == 1:
            a = url[0].split('/')
            dir = a[len(a) - 1]
        else:
            dir = url[1]
        return dir.replace('.git', '')

    @property
    def branch(self):
        return self._branch

    @property
    def url(self):
        return self._data

    @property
    def formatted(self):
        ret = 'b ' + self._branch.ljust(7) + ' ' + self._data.ljust(30)
        return ret

    @property
    def clone(self):
        return 'clone --depth 1 -b {} {}'.format(self.branch, self.url)

    @property
    def pull(self):
        return 'pull'
