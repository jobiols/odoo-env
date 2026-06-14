"""TestRunner — discover, run, report, and gate module tests with coverage.

REQ-QA-001 through REQ-QA-006 (ADR 2–5).
Reuses ``DockerClient``/``RunSpec`` for command assembly so there is a single
docker-command builder for the entire ``oe`` codebase.
"""

import os
import shlex
import subprocess
import sys
from pathlib import Path

from odoo_env.constants import (
    IN_BACKUP_DIR,
    IN_CONFIG,
    IN_CUSTOM_ADDONS,
    IN_DATA,
    IN_LOG,
)
from odoo_env.qa.config import RunnerConfig
from odoo_env.qa.failures import is_error_line
from odoo_env.qa.threshold import check_ratchet, read_floor
from odoo_env.services.docker_client import DockerClient, RunSpec

DEFAULT_COVERAGE_DIR = f"{IN_DATA}/.coverage_data"
DEFAULT_COVERAGE_FILE = f"{DEFAULT_COVERAGE_DIR}/.coverage"


class TestRunner:
    """Orchestrates a full test+coverage run over all modules in a repository."""

    def __init__(self, config: RunnerConfig, docker_client: DockerClient | None = None):
        self.config = config
        self.docker_client = docker_client or DockerClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def discover_test_modules() -> list[str]:
        """Return sorted names of CWD subdirs with ``__manifest__.py`` + ``tests/``.

        Does NOT recurse — only immediate subdirectories are scanned (ADR 3).
        """
        modules = []
        with os.scandir(".") as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                entry_path = Path(entry.path)
                if not (entry_path / "__manifest__.py").is_file():
                    continue
                if not (entry_path / "tests").is_dir():
                    continue
                modules.append(entry.name)
        return sorted(modules)

    def run_all(self) -> bool:
        """Run tests for all discovered modules. Stop on first failure.

        Returns ``True`` when every module passes, ``False`` otherwise.
        """
        modules = self.discover_test_modules()
        if not modules:
            print("No testable modules found.", file=sys.stderr)
            return False

        for module in modules:
            if not self._run_one(module):
                return False
        return True

    def generate_report(self) -> bool:
        """Combine coverage data and produce text/xml/json/html reports.

        Returns ``True`` when reports are generated successfully.
        The ``--fail-under`` flag from ``check_threshold`` must be applied
        here while the coverage data is still available.
        """
        cov_dir = self._coverage_dir
        cov_file = self._coverage_file
        omit = ",".join(self.config.omit)
        floor = self._read_floor()

        inner = (
            f"cd {shlex.quote(cov_dir)} && "
            f"coverage combine && "
            f"coverage report -m --fail-under={floor}"
            f" --omit={shlex.quote(omit)} && "
            f"coverage html -d {shlex.quote(cov_dir + '/htmlcov')}"
            f" --omit={shlex.quote(omit)} && "
            f"coverage xml -o {shlex.quote(cov_dir + '/coverage.xml')}"
            f" --omit={shlex.quote(omit)} && "
            f"coverage json -o {shlex.quote(cov_dir + '/coverage.json')}"
            f" --omit={shlex.quote(omit)}"
        )

        spec = RunSpec(
            image=self.config.image,
            remove=True,
            network=self.config.network,
            volumes=self._normal_volumes,
            entrypoint="bash",
            cmd=["-c", inner],
            env={"COVERAGE_FILE": cov_file},
        )
        cmd = self.docker_client.get_run_command(spec)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0

    def check_threshold(self) -> bool:
        """True when the stored coverage floor passes the ratchet.

        Reads ``.coverage-threshold`` from the repo, compares it against the
        value on ``origin/master`` (ratchet guard), and runs the ratchet.
        Designed for CI / Pull Requests.

        For **enforcement** of measured coverage against the floor, use
        ``generate_report()`` which already applies ``--fail-under``.
        """
        proposed = read_floor(".coverage-threshold")
        try:
            master_raw = subprocess.check_output(
                ["git", "show", "origin/master:.coverage-threshold"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            master = int(master_raw.strip(), 10)
        except subprocess.CalledProcessError:
            master = 20  # no file on master yet → use default
        except ValueError:
            print(
                "WARNING: origin/master:.coverage-threshold is not an integer; "
                f"got {master_raw.strip()!r}. Falling back to 20.",
                file=sys.stderr,
            )
            master = 20

        return check_ratchet(master, proposed)

    # ------------------------------------------------------------------
    # Internal: command building
    # ------------------------------------------------------------------

    @property
    def _normal_volumes(self):
        base = self.config.base_dir
        return {
            f"{base}config": {"bind": IN_CONFIG},
            f"{base}data_dir": {"bind": IN_DATA},
            f"{base}log": {"bind": IN_LOG},
            f"{base}sources": {"bind": IN_CUSTOM_ADDONS},
            f"{base}backup_dir": {"bind": IN_BACKUP_DIR},
        }

    @property
    def _coverage_dir(self) -> str:
        return DEFAULT_COVERAGE_DIR

    @property
    def _coverage_file(self) -> str:
        return DEFAULT_COVERAGE_FILE

    def _build_module_cmd(self, module: str) -> list[str]:
        """Docker command list for running *module*'s tests."""
        if self.config.coverage:
            return self._coverage_module_cmd(module)
        return self._plain_module_cmd(module)

    def _coverage_module_cmd(self, module: str) -> list[str]:
        """Coverage-wrapped: entrypoint=bash, coverage run -p wrapping odoo."""
        source = IN_CUSTOM_ADDONS
        cv_dir = self._coverage_dir
        cv_file = self._coverage_file
        db_name = self.config.db_name

        # DB connection args injected manually because the coverage
        # wrapper (bash -c) skips the regular Odoo entrypoint.
        db_args = (
            "--db_host=db "
            "--db_port=5432 "
            '--db_user="${DB_ENV_POSTGRES_USER:-odoo}" '
            '--db_password="${DB_ENV_POSTGRES_PASSWORD:-odoo}"'
        )

        odoo_cmd = (
            f"coverage run -p --source={shlex.quote(source)} "
            f'"$(command -v odoo)" '
            f"-c {shlex.quote(IN_CONFIG + 'odoo.conf')} "
            f"{db_args} "
            f"--stop-after-init --log-level=test --test-enable "
            f"-d {shlex.quote(db_name)} -i {shlex.quote(module)}"
        )
        inner = f"mkdir -p {shlex.quote(cv_dir)} && {odoo_cmd}"

        spec = RunSpec(
            image=self.config.image,
            interactive=True,
            remove=True,
            network=self.config.network,
            volumes=self._normal_volumes,
            links={f"pg-{self.config.client}": "db"},
            entrypoint="bash",
            cmd=["-c", inner],
            env={"COVERAGE_FILE": cv_file},
        )
        return self.docker_client.get_run_command(spec)

    def _plain_module_cmd(self, module: str) -> list[str]:
        """Plain Odoo test run (no coverage wrapper)."""
        spec = RunSpec(
            image=self.config.image,
            interactive=True,
            remove=True,
            network=self.config.network,
            volumes=self._normal_volumes,
            links={f"pg-{self.config.client}": "db"},
            env={
                "WDB_SOCKET_SERVER": "wdb",
                "WDB_NO_BROWSER_AUTO_OPEN": "True",
                "ODOO_CONF": "/dev/null",
            },
            stop_after_init=True,
            log_level="test",
            test_enable=True,
            extra_args=["-d", self.config.db_name, "-i", module],
        )
        return self.docker_client.get_run_command(spec)

    # ------------------------------------------------------------------
    # Internal: execution + detection
    # ------------------------------------------------------------------

    def _run_one(self, module: str) -> bool:
        """Run *module*'s tests, stream output, detect FAIL/ERROR.

        Returns ``True`` on pass, ``False`` on any failure (exit code or line).
        """
        cmd = self._build_module_cmd(module)

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding="utf-8",
            errors="replace",
        ) as process:
            error_line = None
            for raw_line in process.stdout:
                line = raw_line.rstrip("\r\n")
                print(line, flush=True)
                if error_line is None and is_error_line(line):
                    error_line = line
            process.wait()

        if error_line is not None or process.returncode != 0:
            print(f"\nFAILED: {module}", file=sys.stderr)
            if error_line:
                print(error_line, file=sys.stderr)
            if process.returncode != 0:
                print(f"Exit code: {process.returncode}", file=sys.stderr)
            return False
        return True

    def _read_floor(self) -> int:
        return read_floor(".coverage-threshold")
