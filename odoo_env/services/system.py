from typing import List

class SystemClient:
    def __init__(self, sudo: bool = True):
        self.sudo = sudo

    def _base_cmd(self) -> List[str]:
        return ["sudo"] if self.sudo else []

    def get_mkdir_command(self, path: str, parents: bool = True) -> List[str]:
        cmd = self._base_cmd() + ["mkdir"]
        if parents:
            cmd.append("-p")
        cmd.append(path)
        return cmd

    def get_chmod_command(self, path: str, mode: str, recursive: bool = False) -> List[str]:
        cmd = self._base_cmd() + ["chmod"]
        if recursive:
            cmd.append("-R")
        cmd.extend([mode, path])
        return cmd

    def get_chown_command(self, path: str, user: str, group: str = None, recursive: bool = False) -> List[str]:
        cmd = self._base_cmd() + ["chown"]
        if recursive:
            cmd.append("-R")
        owner = f"{user}:{group}" if group else user
        cmd.extend([owner, path])
        return cmd

    def get_rm_command(self, path: str, recursive: bool = False, force: bool = False) -> List[str]:
        cmd = self._base_cmd() + ["rm"]
        if recursive:
            cmd.append("-r")
        if force:
            cmd.append("-f")
        cmd.append(path)
        return cmd
