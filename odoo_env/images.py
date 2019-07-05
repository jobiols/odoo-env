# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


class Image(object):
    def __init__(self, dict):
        self._dict = dict

    @property
    def short_name(self):
        return self._dict.get('name')

    @property
    def version(self):
        return self._dict.get('ver')

    @property
    def name(self):
        ret = self._dict.get('usr')
        image = self._dict.get('img')
        ver = self._dict.get('ver')

        if image:
            ret += '/' + image
        if ver:
            ret += ':' + ver

        return ret
