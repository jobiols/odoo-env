"""RunnerConfig — the seam between ``oe`` and CI (REQ-QA-007, ADR 1).

A plain dataclass that fully describes a test+coverage run. ``oe`` and the
``python -m odoo_env.qa`` CLI both build it the same way via ``from_oe``, so
there is a single resolution path. Keeping it a dataclass (no globals) makes
the engine environment-agnostic and unit-testable.
"""

from dataclasses import dataclass, field

# Default report omit patterns (REQ-QA-004). They affect reporting only, never
# measurement: the % must reflect production code, not tests/manifests/scripts.
DEFAULT_OMIT = [
    "*/tests/*",
    "*/__manifest__.py",
    "*/test_*.py",
    "*/run_tests.py",
]

# Odoo >=19 no longer loads demo data by default (odoo/odoo#194585); it needs an
# explicit --with-demo flag. For <=18 demo is default-on when installing with -i.
_DEMO_DEFAULT_MAX_VERSION = 18.0


def needs_with_demo_flag(numeric_ver: float) -> bool:
    """True when the Odoo version requires an explicit --with-demo flag.

    Standalone so any -i (install) command builder can apply the same rule,
    not just the ``RunnerConfig``-based engine.
    """
    return numeric_ver > _DEMO_DEFAULT_MAX_VERSION


@dataclass
class RunnerConfig:
    client: str
    version: str
    base_dir: str
    image: str
    db_name: str
    network: str = "odoo-net"
    omit: list[str] = field(default_factory=lambda: list(DEFAULT_OMIT))
    coverage: bool = True
    # The engine always wants demo data for tests; ``numeric_ver`` only decides
    # whether the --with-demo flag must be passed explicitly.
    numeric_ver: float = 0.0

    @classmethod
    def from_oe(cls, client) -> "RunnerConfig":
        """Build a config from an ``oe`` Client, exactly as ``oe`` resolves it."""
        return cls(
            client=client.name,
            version=client.version,
            base_dir=client.base_dir,
            image=client.get_image_required("odoo").name,
            db_name=f"{client.name}_test",
            numeric_ver=client.numeric_ver,
        )

    @property
    def needs_with_demo_flag(self) -> bool:
        """True when the Odoo version requires an explicit --with-demo flag."""
        return needs_with_demo_flag(self.numeric_ver)
