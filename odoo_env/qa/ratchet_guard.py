#!/usr/bin/env python3
"""Ratchet guard — rejects lowering the coverage threshold.

Called by the CI workflow on Pull Requests.
Compares ``.coverage-threshold`` in the PR against the value on
``origin/master``.  Returns non-zero when the PR tries to lower the
floor.
"""
import subprocess
import sys

from odoo_env.qa.threshold import check_ratchet, read_floor


def main() -> int:
    proposed = read_floor(".coverage-threshold")
    master = 20  # default when no file exists on master yet
    try:
        master_raw = subprocess.check_output(
            ["git", "show", "origin/master:.coverage-threshold"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        master = int(master_raw.strip(), 10)
    except (subprocess.CalledProcessError, ValueError):
        pass  # keep the default

    if not check_ratchet(master, proposed):
        print(
            f"RATCHET FAILED: threshold lowered from {master} to {proposed}",
            file=sys.stderr,
        )
        return 1

    print(f"Ratchet OK: {master} -> {proposed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
