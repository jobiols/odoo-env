import re

from odoo_env.messages import msg

# Tag de postgres del estilo pg18 / 0.8.0-pg18 / pg18-bookworm.
# Se busca `pg<digitos>` primero porque en las imagenes pgvector el numero
# que aparece antes es la version de la extension (p.ej. 0.8.0), no la de
# postgres. El lookbehind negativo evita matchear "pg" dentro de una palabra.
_PG_TAG_RE = re.compile(r"(?:^|[^a-z])pg(\d{1,2})(?:[^\d]|$)", re.IGNORECASE)
# Tag numerico clasico: 17.5-alpine, 13, v16, ...
_MAJOR_RE = re.compile(r"^v?(\d{1,2})")

# class Image:
#     def __init__(self, values):
#         self._dict = values

#     @property
#     def short_name(self):
#         return self._dict.get("name")

#     @property
#     def version(self):
#         return self._dict.get("ver")

#     @property
#     def name(self):
#         ret = self._dict.get("usr")
#         image = self._dict.get("img")
#         ver = self._dict.get("ver")

#         if image:
#             ret += "/" + image
#         if ver:
#             ret += ":" + ver

#         return ret


class DockerImage:
    def __init__(self, values, debug=False):
        _odoo_image = "odoo" in values
        values = values.split()
        if len(values) not in (2, 3):
            msg.err(f"Bad image definition {values}")
        self._name = values[0]
        self._url = values[1]
        # Tercer campo opcional: major de postgres declarado explícitamente
        # (para imágenes custom con tags opacos, p.ej. `...:ultima-version 18`).
        self._declared_major = values[2] if len(values) == 3 else None
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
        return ""

    @property
    def name(self):
        return self._url

    @property
    def major_ver(self):
        """Major de postgres, declarado en el manifiesto o derivado del tag.

        El major declarado (tercer campo de la imagen postgres) es
        autoritativo: si está presente, se valida y se usa; un valor inválido
        aborta, sin importar que el tag sea parseable. Si no hay major
        declarado, se deriva del tag (pg18, 0.8.0-pg18, 17.5-alpine, ...). Si
        no hay tag legible ni major declarado, aborta con un error amigable.
        """
        if self._declared_major is not None:
            try:
                return int(self._declared_major)
            except ValueError:
                msg.err(
                    f"Bad postgres major '{self._declared_major}' in image '{self._url}'"
                )
        tag = self._url.split(":")[1] if ":" in self._url else ""
        m = _PG_TAG_RE.search(tag) or _MAJOR_RE.match(tag)
        if not m:
            msg.err(
                f"Cannot determine the postgres version for image '{self._url}'. "
                f"Declare it explicitly with a third field, e.g. "
                f"'postgres {self._url} 18'."
            )
        return int(m.group(1))
