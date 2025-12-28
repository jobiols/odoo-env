class SystemClient:
    def __init__(self):
        pass

    def _base_cmd(self, sudo: bool = False) -> list[str]:
        return ["sudo"] if sudo else []

    def get_mkdir_command(self, path: str, parents: bool = True) -> list[str]:
        cmd = self._base_cmd() + ["mkdir"]
        if parents:
            cmd.append("-p")
        cmd.append(path)
        return cmd

    def get_chmod_command(
        self, path: str, mode: str, recursive: bool = False, sudo: bool = False
    ) -> list[str]:
        cmd = self._base_cmd(sudo) + ["chmod"]
        if recursive:
            cmd.append("-R")
        cmd.extend([mode, path])
        return cmd

    def get_chown_command(
        self,
        path: str,
        user: str = None,
        group: str = None,
        recursive: bool = False,
        sudo: bool = True,
    ) -> list[str]:
        cmd = self._base_cmd(sudo) + ["chown"]
        if recursive:
            cmd.append("-R")
        owner = f"{user}:{group}"
        cmd.extend([owner, path])
        return cmd

    def get_rm_command(
        self, path: str, recursive: bool = False, force: bool = False, sudo: bool = True
    ) -> list[str]:
        cmd = self._base_cmd(sudo) + ["rm"]
        if recursive:
            cmd.append("-r")
        if force:
            cmd.append("-f")
        cmd.append(path)
        return cmd
