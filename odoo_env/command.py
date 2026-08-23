import os
import pty
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import Any

from odoo_env.messages import msg
from odoo_env.odoo_conf import OdooConf
from odoo_env.qa.failures import is_error_line, parse_test_count


class Command:
    def __init__(
        self,
        parent,
        command=None,
        usr_msg=None,
        args=None,
    ):
        """
        :param parent: El objeto OdooEnv que lo contiene por los parametros
        :param command: El comando a ejecutar
        :param usr_msg: El mensaje a mostrarle al usuario
        :param args: Argumentos para chequear, define si se ejecuta o no
        :return: El objeto Comando que se ejecutara luego
        """
        # command/args/usr_msg son dinamicos (str | list | dict | bool segun el
        # subcomando), por eso se anotan como Any.
        self._parent = parent
        self._command: Any = command
        self._usr_msg: Any = usr_msg
        self._args: Any = args

    def check(self):
        # si no tiene argumentos para chequear no requiere chequeo,
        # lo dejamos pasar
        if not self._args:
            return True

        # le pasamos el chequeo al objeto especifico
        return self.check_args()

    def check_args(self) -> bool:
        """Esto no puede ser staticmethod porque al heredarlo usan self._args"""
        return True

    def execute(self):
        self.subprocess_call(self.command)

    @staticmethod
    def _normalize_cmd(cmd):
        """Normaliza el comando a list[str]: split si es str, tal cual si es list."""
        if isinstance(cmd, str):
            return cmd.split()
        if isinstance(cmd, list):
            return cmd
        raise ValueError(f"Invalid command type: {cmd}")

    def subprocess_call(self, cmd, check=True, capture=False):
        """
        Ejecuta un único comando.

        :param cmd: str ("git status") o list[str] (["git", "status"])
        :param check: si True, lanza error si exit code != 0
        :param capture: si True, devuelve (stdout, stderr)
        """
        cmd_run = self._normalize_cmd(cmd)

        # --- Verbose ---
        if self._parent.verbose:
            msg.run(" ")
            msg.run(" ".join(cmd_run))
            msg.run(" ")

        # --- Ejecutar ---
        try:
            completed = subprocess.run(
                cmd_run,
                check=check,
                capture_output=capture,
                text=True,
            )
            if capture:
                return completed.stdout, completed.stderr
            return True
        except subprocess.CalledProcessError as e:
            msg.err(f"Command failed: {e.cmd}\nExit code: {e.returncode}\n{e.stderr}")
        except FileNotFoundError:
            msg.err(f"Command not found: {cmd_run}")
        except OSError as e:
            msg.err(f"Unexpected subprocess error running {cmd_run}: {e}")

    @property
    def args(self):
        return self._args

    @property
    def usr_msg(self):
        return self._usr_msg

    @property
    def command(self):
        return self._command


class CreateGitignore(Command):
    def execute(self):
        # crear el gitignore en el archivo que viene del comando
        values = [".idea/\n", "*.pyc\n", "__pycache__\n"]
        with open(self._command, "w", encoding="utf-8") as _f:
            for value in values:
                _f.write(value)

    def check_args(self):
        return True


class MakedirCommand(Command):
    def check_args(self):
        # si el directorio existe no lo creamos
        return not os.path.isdir(self._args)


class EnsureNetworkCommand(Command):
    """
    Creates a Docker network only when it does not yet exist.

    check_args() runs 'docker network inspect <network>' via subprocess.run
    (no shell=True) to probe whether the network is present:
      - returncode 0  → network exists → return False (skip creation)
      - returncode ≠ 0 → network absent → return True  (proceed to create)

    execute() is inherited from Command unchanged; it runs the
    'docker network create <network>' command passed via command=.
    """

    def check_args(self) -> bool:
        """
        Returns False when the network already exists (skip creation),
        True when it is absent (proceed to create).

        Side effect: spawns 'docker network inspect self._args' with both
        stdout and stderr discarded so no Docker output reaches the user.
        Does NOT raise for any exit code from docker network inspect.
        """
        result = subprocess.run(
            ["docker", "network", "inspect", self._args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode != 0


class RemovedirCommand(Command):
    def check_args(self):
        # si el directorio existe lo borramos
        return os.path.isdir(self._args)


class ExtractSourcesCommand(Command):
    def check_args(self):
        return True


class CloneRepo(Command):
    def check_args(self):
        # si el directorio no existe dejamos clonar
        return not os.path.isdir(self._args)


class PullRepo(Command):
    def check_args(self):
        # si el directorio existe dejamos pulear
        return os.path.isdir(self._args)


class PullImage(Command):
    def check_args(self):
        return True


class WriteConfigFile(Command):
    """Escribe el archivo odoo.conf segun los parametros del manifiesto"""

    def check_args(self):
        return True

    @staticmethod
    def check_item(search_item, search_list):
        for item in search_list:
            if search_item in item:
                return item
        return False

    def execute(self):
        arg = self._args
        client = arg["client"]

        # obtener los repositorios que hay en sources, para eso se recorre souces y se
        # obtienen todos los directorios que tienen un .git adentro.
        repos = []
        base = Path(client.sources_dir)

        manifest_files = list(base.rglob("__manifest__.py"))
        for manifest in manifest_files:
            module_path = str(manifest.parent.parent.relative_to(client.sources_dir))
            if module_path not in repos:
                repos.append(module_path)

        repos = ["/opt/odoo/custom-addons/" + x for x in repos]
        repos = ",".join(repos)

        # Actualizar el archivo odoo.conf

        # Leer el archivo de configuracion original
        odoo_conf = OdooConf(client.config_file)
        odoo_conf.read_config()

        odoo_conf.add_list_data(client.config)

        # siempre sobreescribimos estas tres cosas.
        odoo_conf.add_line(f"addons_path = {repos}")
        odoo_conf.add_line("unaccent = True")
        odoo_conf.add_line("data_dir = /opt/odoo/data")

        # si estoy en modo debug, sobreescribo esto
        if client.debug:
            odoo_conf.add_line("workers = 0")
            odoo_conf.add_line("max_cron_threads = 0")
            odoo_conf.add_line("limit_time_cpu = 0")
            odoo_conf.add_line("limit_time_real = 0")
            odoo_conf.add_line("admin_passwd = admin")
        else:
            # no estoy en modo debug,
            # si no defino workers en el manifiesto lo calculo
            line = self.check_item("workers", client.config)
            if not line:
                # Calculo los workers
                # You should use 2 worker threads per CPU
                odoo_conf.add_line(f"workers = {((os.cpu_count() or 1) * 2)}")
            else:
                odoo_conf.add_line(line)

            # si no defino cron_threads en el manifiesto lo calculo
            line = self.check_item("max_cron_threads", client.config)
            if not line:
                # Calculo los cron threads
                odoo_conf.add_line("max_cron_threads = 1")
            else:
                odoo_conf.add_line(line)

        odoo_conf.write_config()


class MessageOnly(Command):
    def check_args(self):
        """Siempre lo dejamos pasar"""
        return True

    def execute(self):
        """Este metodo debe sobreescribirse en las subclases"""


class TestAllCommand(Command):
    """Runs the full test+coverage engine (REQ-QA-010).

    Delegates to ``TestRunner`` instead of a shell subprocess.
    """

    def __init__(self, parent, runner):
        super().__init__(
            parent,
            usr_msg="Running all module tests with coverage",
        )
        self._runner = runner

    def execute(self):
        self._runner.run_all()
        self._runner.generate_report()


class QaVerdict(Enum):
    """Result of QA stream judgment (REQ-QAJ-001..007)."""

    PASS = auto()
    FAIL_LINE = auto()
    ZERO_TESTS = auto()


class QaCommand(Command):
    """QA test runner with PTY streaming and judgement (REQ-QAJ-001..007).

    Overrides ``execute()`` to stream the docker command through a pseudo
    terminal (colors preserved, no staircase), parse each line for test
    failures and collected test counts, and abort on a detected failure or the
    zero-tests condition instead of trusting Odoo's exit code.
    """

    def __init__(self, parent, command, usr_msg, any_requested_has_tests):
        super().__init__(parent, command=command, usr_msg=usr_msg)
        self._any_requested_has_tests = any_requested_has_tests
        self._exit_code: int | None = None

    def execute(self):
        """Stream + judge the QA run and abort on failure or zero-tests.

        Decision order (ADR-3): FAIL_LINE -> non-zero exit -> ZERO_TESTS.
        ``msg.err`` prints AND raises ``OeError``, so each branch aborts at the
        first condition that fires.
        """
        lines = self._stream_lines(self.command)
        verdict = self._judge_stream(lines, self._any_requested_has_tests)

        if verdict is QaVerdict.FAIL_LINE:
            msg.err("Test failure detected")
        if self._exit_code != 0:
            msg.err(f"Odoo exited with code {self._exit_code}")
        if verdict is QaVerdict.ZERO_TESTS:
            msg.err(
                "0 tests collected: the requested module(s) have a tests/ "
                "directory but Odoo collected no tests (issue #128)."
            )

    def _stream_lines(self, cmd):
        """Run *cmd* through a pseudo-terminal and yield decoded lines.

        The ONLY pty/os.read/Popen surface (REQ-QAJ-006..007): spawns the docker
        command with the PTY slave as stdout/stderr, reads the master fd until
        EOF (EIO on child exit), buffers partial lines, and yields each complete
        line decoded with UTF-8 replacement. The child exit code is captured on
        ``self._exit_code`` for ``execute()``.

        MANUAL REAL-RUN CHECKLIST (REQ-QAJ-006, cannot be unit-tested without
        Docker): before merge, run ``oe -Q <module_with_a_colored_failing_test>``
        and confirm on a real terminal that (a) ANSI colors are preserved on the
        console, and (b) no staircase/rightward cascade appears. The mocked-pty
        loop tests (TestPtySeam) verify buffering/EIO/decode/exit-code only.
        """
        # pylint: disable=consider-using-with
        # Raw-FD seam is intentionally `with`-free: TestPtySeam patches
        # os.read/os.close/Popen exactly, so os.fdopen + context managers
        # would break the mocked seam.
        master, slave = pty.openpty()
        try:
            process = subprocess.Popen(
                cmd,
                stdout=slave,
                stderr=slave,
                close_fds=True,
            )
            os.close(slave)

            buffer = b""
            while True:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    # EIO on child exit — normal EOF for PTY reads.
                    break
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    yield line.decode("utf-8", errors="replace")

            if buffer:
                yield buffer.decode("utf-8", errors="replace")

            process.wait()
            self._exit_code = process.returncode
        finally:
            os.close(master)

    def _judge_stream(self, lines, any_has_tests):
        """Consume *lines*, reprint to stdout, detect failures and counts.

        Pure decision logic (REQ-QAJ-001..005): reprints every line verbatim
        (colors intact, flushed), flags any ``is_error_line`` match, and
        aggregates every ``parse_test_count`` match. Returns the appropriate
        ``QaVerdict``. Exit code is NOT inspected here (``execute()``'s job).
        """
        aggregate = 0
        failure = False
        for line in lines:
            print(line, flush=True)
            if is_error_line(line):
                failure = True
            count = parse_test_count(line)
            if count is not None:
                aggregate += count

        if failure:
            return QaVerdict.FAIL_LINE
        if aggregate == 0 and any_has_tests:
            return QaVerdict.ZERO_TESTS
        return QaVerdict.PASS
