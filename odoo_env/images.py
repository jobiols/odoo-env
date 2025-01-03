from odoo_env.messages import Msg

msg = Msg()


class Image:
    def __init__(self, values):
        self._dict = values

    @property
    def short_name(self):
        return self._dict.get("name")

    @property
    def version(self):
        return self._dict.get("ver")

    @property
    def name(self):
        ret = self._dict.get("usr")
        image = self._dict.get("img")
        ver = self._dict.get("ver")

        if image:
            ret += "/" + image
        if ver:
            ret += ":" + ver

        return ret


class Image2:
    def __init__(self, values, debug=False):
        _odoo_image = "odoo" in values
        values = values.split()
        if len(values) != 2:
            msg.err(f"Bad image definition {values}")
        self._name = values[0]
        self._url = values[1]
        if _odoo_image and debug:
            self._url += ".debug"

    @property
    def short_name(self):
        return self._name

    @property
    def version(self):
        a = self._url
        ver = a.split(":")
        if len(ver) == 2:
            return ver[1]
        else:
            return ""

    @property
    def name(self):
        return self._url
