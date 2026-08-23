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

# Matches Odoo's test summary line: "0 failed, 0 error(s) of 5 tests".
# Only the "of <N> tests" fragment is captured; the count is the aggregate
# across every summary line (install + update phases).
TEST_COUNT_PATTERN = re.compile(r"of (\d+) tests")


def strip_ansi(line: str) -> str:
    """Return *line* with ANSI escape/control sequences removed."""
    return ANSI_ESCAPE.sub("", line)


def is_error_line(line: str) -> bool:
    """True when *line* indicates a failed/errored Odoo test."""
    return bool(ERROR_PATTERN.search(strip_ansi(line)))


def parse_test_count(line: str) -> int | None:
    """Extract the test count from an Odoo test summary line.

    Returns the integer N for a line containing "of N tests", or None when the
    line is not a summary line. ANSI escape sequences are stripped before
    matching (consistent with ``is_error_line``). Returns ``None`` (never ``0``)
    for non-matches so aggregation never miscounts an unrelated line as 0 tests.

    Examples:
        "0 failed, 0 error(s) of 5 tests" -> 5
        "INFO: Modules loaded." -> None
    """
    match = TEST_COUNT_PATTERN.search(strip_ansi(line))
    # pi-lens-ignore: unchecked-throwing-call-python - group(1) is \d+ (see
    # TEST_COUNT_PATTERN), so int() can never raise; None is returned on no match.
    return int(match.group(1)) if match else None
