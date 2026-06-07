from collections.abc import Mapping
from dataclasses import dataclass


@dataclass
class RunSpec:
    """Parametros para construir un `docker run`.

    Agrupa las (muchas) opciones de `docker run` en un solo objeto para
    mantener la firma de `DockerClient.get_run_command` acotada y tipada.
    """

    image: str
    cmd: str | list[str] | None = None
    detach: bool = False
    remove: bool = False
    interactive: bool = False
    name: str | None = None
    ports: dict[int, int] | None = None
    volumes: Mapping[str, dict[str, str] | str] | None = None
    env: dict[str, str] | None = None
    links: dict[str, str] | None = None
    network: str | None = None
    restart: str | None = None
    user: str | None = None
    entrypoint: str | None = None
    workdir: str | None = None
    stop_after_init: bool = False
    logfile: str | None = None
    log_level: str | None = None
    test_enable: bool = False
    extra_args: list[str] | None = None
    database: str | None = None


class DockerClient:

    @staticmethod
    def _base_cmd() -> list[str]:
        return ["docker"]

    # ---------- helpers internos ----------

    def _apply_basic_flags(self, cmd: list[str], spec: RunSpec) -> None:
        if spec.detach:
            cmd.append("-d")
        if spec.remove:
            cmd.append("--rm")
        if spec.interactive:
            cmd.append("-it")

    def _apply_runtime_options(self, cmd: list[str], spec: RunSpec) -> None:
        if spec.name:
            cmd.extend(["--name", spec.name])
        if spec.network:
            cmd.extend(["--network", spec.network])
        if spec.restart:
            cmd.extend(["--restart", spec.restart])
        if spec.user:
            cmd.extend(["--user", spec.user])
        if spec.entrypoint:
            cmd.extend(["--entrypoint", spec.entrypoint])
        if spec.workdir:
            cmd.extend(["-w", spec.workdir])

    def _apply_ports(self, cmd: list[str], ports: dict[int, int] | None) -> None:
        if not ports:
            return
        for host, container in ports.items():
            cmd.extend(["-p", f"{host}:{container}"])

    def _apply_volumes(
        self,
        cmd: list[str],
        volumes: Mapping[str, dict[str, str] | str] | None,
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

    def _apply_odoo_args(self, cmd: list[str], spec: RunSpec) -> None:
        if spec.stop_after_init:
            cmd.append("--stop-after-init")

        if spec.logfile is not None:
            if spec.logfile == "false":
                cmd.append("--logfile=false")
            else:
                cmd.append(f"--logfile={spec.logfile}")

        if spec.log_level:
            cmd.append(f"--log-level={spec.log_level}")

        if spec.test_enable:
            cmd.append("--test-enable")

    def _apply_cmd(self, cmd_list: list[str], command: str | list[str] | None) -> None:
        if not command:
            return
        if isinstance(command, str):
            cmd_list.extend(command.split())
        else:
            cmd_list.extend(command)

    def _apply_database(self, cmd: list[str], database: str | None) -> None:
        if not database:
            return
        cmd.extend(["-d", database])

    def get_stop_command(self, container_name: str) -> list[str]:
        return ["docker", "stop", container_name]

    def get_rm_command(self, container_name: str) -> list[str]:
        return ["docker", "rm", container_name]

    def get_pull_command(self, image: str) -> list[str]:
        return ["docker", "pull", image]

    def get_extract_cp_command(
        self,
        image: str,
        container_src: str,
        host_dest: str,
        mount: str = "/oe-extract-dest",
    ) -> list[str]:
        """Copia `container_src` de la imagen al host SIN arrancar odoo.

        Usa `docker run --entrypoint cp`: reemplaza el entrypoint de odoo por
        `cp`, asi que odoo NO arranca. El `cp -a` corre DENTRO del contenedor
        y preserva los symlinks tal cual. (`docker cp`, en cambio, valida los
        symlinks que escapan del arbol copiado y rompe con, p.ej.,
        `babel/global.dat -> ../../../../share/python-babel-localedata/...`).
        El dir host se monta en `mount` y se copia el CONTENIDO de src (src/.).
        """
        return [
            "docker",
            "run",
            "--rm",
            "--user",
            "root",
            "--entrypoint",
            "cp",
            "-v",
            f"{host_dest}:{mount}",
            image,
            "-a",
            f"{container_src.rstrip('/')}/.",
            f"{mount}/",
        ]

    # ---------- API pública ----------

    def get_run_command(self, spec: RunSpec) -> list[str]:
        command = self._base_cmd() + ["run"]

        self._apply_basic_flags(command, spec)
        self._apply_runtime_options(command, spec)
        self._apply_ports(command, spec.ports)
        self._apply_volumes(command, spec.volumes)
        self._apply_env(command, spec.env)
        self._apply_links(command, spec.links)

        command.append(spec.image)

        self._apply_odoo_args(command, spec)

        if spec.extra_args:
            command.extend(spec.extra_args)

        self._apply_cmd(command, spec.cmd)
        self._apply_database(command, spec.database)

        return command

    @staticmethod
    def get_network_create_command(network: str) -> list[str]:
        return ["docker", "network", "create", network]
