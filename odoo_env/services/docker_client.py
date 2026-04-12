class DockerClient:

    @staticmethod
    def _base_cmd() -> list[str]:
        return ["docker"]

    # ---------- helpers internos ----------

    def _apply_basic_flags(
        self,
        cmd: list[str],
        detach: bool,
        remove: bool,
        interactive: bool,
    ) -> None:
        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        if interactive:
            cmd.append("-it")

    # pylint: disable=too-many-arguments
    def _apply_runtime_options(
        self,
        cmd: list[str],
        name: str | None,
        network: str | None,
        restart: str | None,
        user: str | None,
        entrypoint: str | None,
        workdir: str | None,
    ) -> None:
        if name:
            cmd.extend(["--name", name])
        if network:
            cmd.extend(["--network", network])
        if restart:
            cmd.extend(["--restart", restart])
        if user:
            cmd.extend(["--user", user])
        if entrypoint:
            cmd.extend(["--entrypoint", entrypoint])
        if workdir:
            cmd.extend(["-w", workdir])

    def _apply_ports(self, cmd: list[str], ports: dict[int, int] | None) -> None:
        if not ports:
            return
        for host, container in ports.items():
            cmd.extend(["-p", f"{host}:{container}"])

    def _apply_volumes(
        self,
        cmd: list[str],
        volumes: dict[str, dict[str, str] | str] | None,
    ) -> None:
        if not volumes:
            return

        for host_path, vol_data in volumes.items():
            if isinstance(vol_data, str):
                bind = vol_data
                mode = "rw"
            else:
                bind = vol_data.get("bind")
                mode = vol_data.get("mode", "rw")
            cmd.extend(["-v", f"{host_path}:{bind}:{mode}"])

    def _apply_env(self, cmd: list[str], env: dict[str, str] | None) -> None:
        if not env:
            return
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])

    def _apply_links(self, cmd: list[str], links: dict[str, str] | None) -> None:
        if not links:
            return
        for target, alias in links.items():
            cmd.extend(["--link", f"{target}:{alias}"])

    def _apply_odoo_args(
        self,
        cmd: list[str],
        stop_after_init: bool,
        logfile: str | None,
        log_level: str | None,
        test_enable: bool,
    ) -> None:
        if stop_after_init:
            cmd.append("--stop-after-init")

        if logfile is not None:
            if logfile == "false":
                cmd.append("--logfile=false")
            else:
                cmd.append(f"--logfile={logfile}")

        if log_level:
            cmd.append(f"--log-level={log_level}")

        if test_enable:
            cmd.append("--test-enable")

    def _apply_cmd(self, cmd: list[str], command: str | list[str] | None) -> None:
        if not command:
            return
        if isinstance(command, str):
            cmd.extend(command.split())
        else:
            cmd.extend(command)

    def _apply_database(self, cmd: list[str], database: str | None) -> None:
        if not database:
            return
        cmd.extend(["-d", database])

    def get_stop_command(self, container_name: str) -> list[str]:
        return ["docker", "stop", container_name]

    def get_rm_command(
        self,
        container_name: str,
        recursive: bool = False,
        force: bool = False,
        sudo: bool = True,
    ) -> list[str]:
        return ["docker", "rm", container_name]

    def get_pull_command(self, image: str) -> list[str]:
        return ["docker", "pull", image]

    # ---------- API pública (SIN CAMBIOS) ----------
    # pylint: disable=too-many-arguments
    def get_run_command(
        self,
        image: str,
        cmd: str | list[str] | None = None,
        detach: bool = False,
        remove: bool = False,
        interactive: bool = False,
        name: str | None = None,
        ports: dict[int, int] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        env: dict[str, str] | None = None,
        links: dict[str, str] | None = None,
        network: str | None = None,
        restart: str | None = None,
        user: str | None = None,
        entrypoint: str | None = None,
        workdir: str | None = None,
        stop_after_init: bool = False,
        logfile: str | None = None,
        log_level: str | None = None,
        test_enable: bool = False,
        extra_args: list[str] | None = None,
        database: str | None = None,
        network_alias: str | None = None,  # se deja para compatibilidad
    ) -> list[str]:

        command = self._base_cmd() + ["run"]

        self._apply_basic_flags(command, detach, remove, interactive)
        self._apply_runtime_options(
            command, name, network, restart, user, entrypoint, workdir
        )
        self._apply_ports(command, ports)
        self._apply_volumes(command, volumes)
        self._apply_env(command, env)
        self._apply_links(command, links)

        command.append(image)

        self._apply_odoo_args(command, stop_after_init, logfile, log_level, test_enable)

        if extra_args:
            command.extend(extra_args)

        self._apply_cmd(command, cmd)

        self._apply_database(command, database)

        return command

    @staticmethod
    def get_network_create_command(network: str) -> list[str]:
        return ["docker", "network", "create", network]
