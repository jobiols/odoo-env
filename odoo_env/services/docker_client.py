from typing import Optional, Union


class DockerClient:
    def __init__(self):
        pass

    def _base_cmd(self) -> list[str]:
        return ["docker"]

    def get_run_command(
        self,
        image: str,
        cmd: Optional[Union[str, list[str]]] = None,
        detach: bool = False,
        remove: bool = False,
        interactive: bool = False,
        name: Optional[str] = None,
        ports: dict[int, int] = None,
        volumes: dict[str, dict[str, str]] = None,
        env: dict[str, str] = None,
        links: dict[str, str] = None,
        network: str = None,
        restart: str = None,
        user: str = None,
        entrypoint: str = None,
        workdir: str = None,
        stop_after_init: bool = False,
        logfile: str = None,
        log_level: str = None,
        test_enable: bool = False,
        extra_args: list[str] = None,
        network_alias: str = None,
    ) -> list[str]:

        command = self._base_cmd() + ["run"]
        if detach:
            command.append("-d")
        if remove:
            command.append("--rm")
        if interactive:
            command.append("-it")
        if name:
            command.extend(["--name", name])
        if network:
            command.extend(["--network", network])
        if restart:
            command.extend(["--restart", restart])
        if user:
            command.extend(["--user", user])
        if entrypoint:
            command.extend(["--entrypoint", entrypoint])
        if workdir:
            command.extend(["-w", workdir])
        if ports:
            for host, container in ports.items():
                command.extend(["-p", f"{host}:{container}"])

        if volumes:
            for host_path, vol_data in volumes.items():
                if isinstance(vol_data, str):
                    bind = vol_data
                    mode = "rw"
                else:
                    bind = vol_data.get("bind")
                    mode = vol_data.get("mode", "rw")
                command.extend(["-v", f"{host_path}:{bind}:{mode}"])

        if env:
            for k, v in env.items():
                command.extend(["-e", f"{k}={v}"])

        if links:
            for target, alias in links.items():
                command.extend(["--link", f"{target}:{alias}"])

        command.append(image)

        # Odoo specific args that go AFTER the image
        if stop_after_init:
            command.append("--stop-after-init")

        if logfile is not None:
            if logfile == "false":
                command.append("--logfile=false")
            else:
                command.append(f"--logfile={logfile}")

        if log_level:
            command.append(f"--log-level={log_level}")

        if test_enable:
            command.append("--test-enable")

        if extra_args:
            command.extend(extra_args)

        if cmd:
            if isinstance(cmd, str):
                command.extend(cmd.split())
            else:
                command.extend(cmd)

        return command

    def get_stop_command(self, container: str) -> list[str]:
        return self._base_cmd() + ["stop", container]

    def get_rm_command(self, container: str, force: bool = False) -> list[str]:
        cmd = self._base_cmd() + ["rm"]
        if force:
            cmd.append("-f")
        cmd.append(container)
        return cmd

    def get_pull_command(self, image: str) -> list[str]:
        return self._base_cmd() + ["pull", image]

    def get_network_create_command(self, network: str) -> str:
        return f"docker network create {network} 2>/dev/null || true"
