"""Reliable Odoo test-failure detection (REQ-QA-003, ADR 4).

Odoo can return a process exit code of 0 even when a unit test fails, so a CI
gate cannot trust the exit code alone. This module ports the proven detection
from the reference ``run_tests.py``: strip ANSI escapes, then match the
unittest failure marker ``: FAIL:`` / ``: ERROR:`` followed by a word char
(the trailing ``\\w`` avoids false positives like ``bad query:`` or
``unique constraint``).
"""

import re

# Strip ANSI colour/control sequences Docker may emit even with plain output.
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|[\x07\x08\x0d]")

# Matches a unittest result line: ": FAIL: TestXxx" or ": ERROR: TestXxx".
# The final \w prevents false positives such as "bad query:" or
# "violates unique constraint".
ERROR_PATTERN = re.compile(r":\s+(FAIL|ERROR): \w")


def strip_ansi(line: str) -> str:
    """Return *line* with ANSI escape/control sequences removed."""
    return ANSI_ESCAPE.sub("", line)


def is_error_line(line: str) -> bool:
    """True when *line* indicates a failed/errored Odoo test."""
    return bool(ERROR_PATTERN.search(strip_ansi(line)))
