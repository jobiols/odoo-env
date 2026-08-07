"""CLI entrypoint for the qa-coverage engine — ``python -m odoo_env.qa``.

Builds a ``RunnerConfig`` from the oe manifest of the checked-out repo,
discovers all testable Odoo modules, runs their tests with coverage, and
enforces the coverage threshold.

Usage from a client repo::

    python -m odoo_env.qa

Exit code 0 when all tests pass and coverage meets the floor; non-zero
otherwise.
"""

import sys

from odoo_env.client import Client
from odoo_env.config import OeConfig
from odoo_env.qa.config import RunnerConfig
from odoo_env.qa.runner import TestRunner


def main() -> int:
    config = RunnerConfig.from_oe(_oe_client())
    runner = TestRunner(config)

    if not runner.run_all():
        return 1

    if not runner.generate_report():
        print("Coverage report generation failed.", file=sys.stderr)
        return 1

    return 0


def _oe_client() -> Client:
    """Create a one-shot Client from the current oe config."""
    conf = OeConfig()
    client_name = conf.get_client()
    if not client_name:
        print(
            "No default client configured. Run 'oe -c <client>' first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return Client(MockArgs(client=client_name), name=client_name)


class MockArgs:
    """Trivial namespace so Client.__init__ receives an args-like object."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.__dict__.setdefault("install", False)


if __name__ == "__main__":
    sys.exit(main())
