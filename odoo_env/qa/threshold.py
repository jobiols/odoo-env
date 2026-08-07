"""Coverage threshold floor + ratchet (REQ-QA-005/006, ADR 6).

The floor lives in a repo-versioned ``.coverage-threshold`` file (a single
integer, default 20). It is easy to edit and diff. The ratchet guard compares
a Pull Request's proposed floor against the value on ``master``: lowering the
floor is rejected, raising (or keeping) it is allowed.

Enforcement of the measured coverage against the floor is done by coverage
itself via ``coverage report --fail-under=<floor>`` (exit 2 on failure); this
module only owns *reading* and *ratcheting* the stored floor.
"""

from pathlib import Path

DEFAULT_FLOOR = 20


def read_floor(path) -> int:
    """Return the stored coverage floor.

    A *missing* file means "not configured yet" and yields ``DEFAULT_FLOOR``.
    A *present but malformed* file is a misconfiguration and raises a clear
    ``ValueError`` (rather than silently falling back, which could weaken the
    gate/ratchet without anyone noticing).
    """
    p = Path(path)
    if not p.is_file():
        return DEFAULT_FLOOR
    raw = p.read_text(encoding="utf-8").strip()
    try:
        value = int(raw, 10)
    except ValueError as exc:
        raise ValueError(
            f"Invalid coverage floor in {p}: expected an integer 0-100, got {raw!r}"
        ) from exc
    if not 0 <= value <= 100:
        raise ValueError(
            f"Coverage floor in {p} must be between 0 and 100, got {value}"
        )
    return value


def check_ratchet(master: int, proposed: int) -> bool:
    """True when *proposed* floor does not lower the *master* floor."""
    return proposed >= master
