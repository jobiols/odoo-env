import re

from odoo_env.messages import Msg


class Repo:
    def __init__(self, value):
        self._dict = value

    @property
    def name(self):
        return self._dict.get("repo")

    @property
    def dir_name(self):
        return self._dict.get("repo")

    @property
    def branch(self):
        return self._dict.get("branch")

    @property
    def url(self):
        if self._dict.get("ssh", False):
            template = "git@{}:{}/{}"
        else:
            template = "https://{}/{}/{}"

        return template.format(
            self._dict.get("host", "github.com"),
            self._dict.get("usr"),
            self._dict.get("repo"),
        )

    @property
    def formatted(self):
        aaa = self._dict["usr"] + "/" + self._dict["repo"]
        ret = "b " + self._dict["branch"].ljust(7) + " " + aaa.ljust(30)
        return ret

    @property
    def clone(self):
        return f"clone --depth 1 -b {self.branch} {self.url}"

    @property
    def pull(self):
        return "pull"


class Repo2:
    def __init__(self, value, branch, options):
        """Sintaxis <repo> [<directory>[/<directory>] [-b <branch>] [optios]
        El branch debe estar despues del repo, si no esta se toma el branch
        que viene como parametro, si no viene nada es una excepcion.
        El directorio va despues del repo y puede no estar
        """
        # parsear value en una lista
        parsed = value.split(" ")
        # eliminar los espacios
        parsed = [i for i in parsed if i != ""]

        if "--recurse-submodules" in parsed:
            parsed.remove("--recurse-submodules")
            self._recurse_submodules = True
        else:
            self._recurse_submodules = False

        # obtener el branch si es que existe
        if "-b" in parsed:
            index = parsed.index("-b")
            self._branch = parsed[index + 1]
            # eliminar el -b y el parametro branch
            parsed.remove("-b")
            parsed.remove(self._branch)
        else:
            self._branch = branch

        self._url = parsed[0]

        # agregarle a la url el prefijo de ssh si es requerido solo si estamos en produccion
        if self.protocol == "ssh" and not options["debug"]:
            self._url = re.sub(r"@(github)", f"@{self.code_name}.\\1", self._url)

        # si me quedan dos parametros tengo un directorio
        if len(parsed) > 1:
            self._dir = parsed[1]
            self._extra_dir = True
        else:
            parsed = self._url.split("/")
            self._dir = parsed[len(parsed) - 1].replace(".git", "")
            self._extra_dir = False

    @property
    def dir_name(self):
        """Obtener el directorio donde se pone el repo"""
        return self._dir

    @property
    def branch(self):
        return self._branch

    @property
    def url(self):
        if self._extra_dir:
            return f"{self._url} {self._dir}"
        else:
            return self._url

    @property
    def formatted(self):
        recurse = "recursive" if self._recurse_submodules else ""
        if self._extra_dir:
            return f"b {self.branch} {recurse}    {self._url} >> {self._dir}"
        else:
            return f"b {self.branch} {recurse}    {self.url}"

    @property
    def clone(self):
        recurse = "--recurse-submodules" if self._recurse_submodules else ""
        return f"clone --depth 1 {recurse} -b {self.branch} {self.url}"

    @property
    def pull(self):
        recurse = "--recurse-submodules" if self._recurse_submodules else ""
        return f"pull {recurse}"

    @property
    def protocol(self):
        if self._url.startswith("git@"):
            return "ssh"
        if self._url.startswith("https:"):
            return "https"
        Msg().err(f"Unknown git protocol {self._url}")

    @property
    def code_name(self):
        """Obtener el nombre del repositorio del"""
        pattern = r"[:/](?P<name>[^/]+?)(?:\.git|\s|$)"
        match = re.search(pattern, self._url)
        if match:
            return match.group("name")

        Msg.err(f"invalid repository URL {self._url}")
