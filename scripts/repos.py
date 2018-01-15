# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


class Repo(object):
    def __init__(self, dict):
        self._dict = dict

    @property
    def dir_name(self):
        return self._dict.get('repo')

    @property
    def branch(self):
        return self._dict.get('branch')

    @property
    def url(self):
        return 'https://github.com/{}/{}'.format(self._dict.get('usr'),
                                                 self._dict.get('repo'))

    @property
    def formatted(self):
        aaa = self._dict['usr'] + '/' + self._dict['repo']
        ret = 'b ' + self._dict['branch'].ljust(7) + ' ' + aaa.ljust(30)
        return ret

    @property
    def clone(self):
        return 'clone -b {} {}'.format(self.branch, self.url)

    @property
    def pull(self):
        return 'pull'

