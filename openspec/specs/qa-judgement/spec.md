# qa-judgement Specification

## Purpose

Defines how the interactive `oe -Q <modules>` command **judges** the result of an
Odoo test run instead of trusting Odoo's exit code. Odoo exits `0` even when a
unit test FAILs/ERRORs and even when `0 tests` are collected, so a gate built on
the exit code alone reports false greens. This change turns `oe -Q` into a real QA
gate by streaming Odoo's output through a pseudo-terminal (pty), parsing each line,
and aborting on a detected failure or on the zero-tests condition.

This spec covers only the interactive `oe -Q` execution/judgement path (Part B of
issue #128). It does **not** cover per-module verb selection (`-i` vs `-u`, Part A
— already specified in the `qa-verb` domain) and does **not** merge the `oe -Q`
executor with the CI runner (`odoo_env/qa/runner.py`). See Non-Requirements.

The judgement is expressed as **two independent gates**; either one aborts the run:

1. **Failure-line gate** — the run aborts when any streamed line matches the
   existing failure detector `is_error_line` (after ANSI strip).
2. **Zero-tests gate** — the run aborts when the **aggregate collected test count
   is 0** AND **at least one requested module has a `tests/` directory**.

A run is reported as success only when neither gate fires.

## Requirements

### Requirement: REQ-QAJ-001 — A real test failure aborts `oe -Q`

When `oe -Q <module>` is invoked and the Odoo output contains a line that matches
the existing failure pattern (`: FAIL:` or `: ERROR:`, detected by `is_error_line`
after ANSI escape stripping), the system MUST abort with an error (`msg.err`) and a
non-zero result. The system MUST NOT report success for that run.

Failure detection MUST reuse the existing, proven detector
`odoo_env/qa/failures.py::is_error_line` unchanged. The system MUST NOT introduce
new failure-detection logic or a new failure regex.

#### Scenario: A `: FAIL:` line aborts the run

- GIVEN `oe -Q my_module` is invoked
- AND the streamed Odoo output contains a line such as
  `2026-01-01 00:00:00,000 1 INFO test_db odoo.addons.my_module.tests.test_x: FAIL: TestX.test_y`
- WHEN that line is streamed and inspected
- THEN the line MUST be classified as a failure by `is_error_line`
- AND `oe -Q` MUST abort via `msg.err` with a non-zero result
- AND the run MUST NOT be reported as success

#### Scenario: A `: ERROR:` line aborts the run

- GIVEN `oe -Q my_module` is invoked
- AND the streamed Odoo output contains a line matching `: ERROR:` for a test
- WHEN that line is streamed and inspected
- THEN the line MUST be classified as a failure by `is_error_line`
- AND `oe -Q` MUST abort via `msg.err` with a non-zero result

#### Scenario: Failure detection tolerates ANSI color codes

- GIVEN `oe -Q my_module` is invoked with colors enabled
- AND the streamed output contains a failure line wrapped in ANSI color/control
  sequences
- WHEN that line is inspected
- THEN `is_error_line` MUST strip the ANSI sequences before matching
- AND the line MUST still be classified as a failure
- AND `oe -Q` MUST abort

#### Scenario: Unrelated text is not a failure

- GIVEN `oe -Q my_module` is invoked
- AND the streamed output contains a line with text such as `bad query:` or
  `violates unique constraint` that does not carry the `: FAIL:` / `: ERROR:`
  marker followed by a word character
- WHEN that line is inspected
- THEN `is_error_line` MUST NOT classify it as a failure
- AND the run MUST continue (subject to the zero-tests gate)

### Requirement: REQ-QAJ-002 — Zero tests with a `tests/` directory aborts

When `oe -Q <modules>` is invoked, the system MUST compute the aggregate collected
test count as the sum of every `of (\d+) tests` summary line in the streamed output.
If the aggregate collected test count is `0` AND at least one requested module has a
`tests/` directory, the system MUST abort with an explicit "0 tests collected"
error (issue #128) and a non-zero result. The system MUST NOT report success.

The precise zero-tests criterion is:

> ERROR when **(aggregate test count == 0)** AND **(at least one requested module
> has a `tests/` directory)**.

#### Scenario: A requested module with a `tests/` dir collects 0 tests

- GIVEN the requested module `my_module` has a `tests/` directory on disk
- AND the streamed output contains the summary line `0 failed, 0 error(s) of 0 tests`
- AND no failure line appears
- WHEN `oe -Q my_module` finishes streaming
- THEN the aggregate collected test count MUST be `0`
- AND the system MUST abort with an explicit "0 tests collected" error
- AND the system MUST NOT report success

#### Scenario: Aggregate of 0 across multiple summary lines still aborts

- GIVEN the requested modules include `my_module` which has a `tests/` directory
- AND the streamed output contains two summary lines, e.g. one `... of 0 tests`
  from the install phase and one `... of 0 tests` from the update phase
- WHEN `oe -Q my_module` finishes streaming
- THEN the aggregate collected test count MUST be `0` (the sum of the two counts)
- AND the system MUST abort with the "0 tests collected" error

#### Scenario: A partial count that is non-zero does not trigger the zero-tests gate

- GIVEN the requested modules include `my_module` which has a `tests/` directory
- AND the streamed output contains summary lines that aggregate to a non-zero count
  (e.g. `... of 2 tests` plus `... of 3 tests`)
- WHEN `oe -Q my_module` finishes streaming
- THEN the aggregate collected test count MUST be `6` (non-zero)
- AND the zero-tests gate MUST NOT fire
- AND the run MUST NOT be aborted for the zero-tests condition

### Requirement: REQ-QAJ-003 — Zero tests without any `tests/` directory passes

When `oe -Q <modules>` is invoked and **no** requested module has a `tests/`
directory, a collected test count of `0` is legitimate. In that case the system
MUST pass (report success) and MUST NOT raise the "0 tests collected" error.

#### Scenario: No requested module has a `tests/` dir

- GIVEN the requested modules are `mod_a` and `mod_b`
- AND neither `mod_a` nor `mod_b` has a `tests/` directory on disk
- AND the streamed output reports `of 0 tests`
- AND no failure line appears
- WHEN `oe -Q mod_a,mod_b` finishes streaming
- THEN the system MUST report success
- AND the system MUST NOT raise the "0 tests collected" error

### Requirement: REQ-QAJ-004 — A passing run with collected tests reports success

When `oe -Q <modules>` collects a non-zero aggregate test count (a summary line
matching `of N tests` with `N > 0`) and no failure line appears, the system MUST
report success.

#### Scenario: Tests collected with no failures

- GIVEN `oe -Q my_module` is invoked
- AND the streamed output contains `0 failed, 0 error(s) of 5 tests`
- AND no `: FAIL:` or `: ERROR:` line appears
- WHEN `oe -Q my_module` finishes streaming
- THEN the aggregate collected test count MUST be `5` (non-zero)
- AND the system MUST report success

### Requirement: REQ-QAJ-005 — `parse_test_count` extracts and aggregates counts

The system MUST provide a parser `parse_test_count(line) -> int | None` in
`odoo_env/qa/failures.py` with the following behavior:

- It MUST return the integer `N` for a line matching `of (\d+) tests`.
- It MUST return `None` (no match) for any line that does not contain an
  `of <N> tests` summary.
- It MUST NOT treat `None` as a count of `0`.

The QA judgement MUST sum the integer results from **every** summary line it sees
(e.g. across `-i` and `-u` phases), and MUST use that aggregate as the collected
test count for the zero-tests criterion. The zero-tests condition is
**aggregate == 0**, not "no summary line seen".

#### Scenario: Summary line yields its count

- GIVEN the line `2026-01-01 00:00:00,000 1 INFO test_db odoo.modules.loading: Modules loaded.`
  is followed by a summary line `0 failed, 0 error(s) of 5 tests`
- WHEN `parse_test_count` is called on the summary line
- THEN it MUST return `5`
- AND when called on the unrelated `Modules loaded.` line it MUST return `None`

#### Scenario: Non-summary lines return None

- GIVEN the line `2026-01-01 00:00:00,000 1 INFO test_db odoo.modules.loading: Modules loaded.`
- WHEN `parse_test_count` is called
- THEN it MUST return `None`

#### Scenario: Multiple summary lines are summed

- GIVEN the streamed output contains `... of 2 tests` and later `... of 3 tests`
- WHEN the judgement aggregates the counts
- THEN the aggregate collected test count MUST be `5`
- AND the zero-tests gate MUST use `5`, not the last count seen

#### Scenario: No summary line is not a zero-tests trigger by itself

- GIVEN no `of <N> tests` summary line appears in the output
- WHEN `parse_test_count` is applied to every streamed line
- THEN every call MUST return `None`
- AND the aggregate collected test count MUST remain `0`
- AND the zero-tests gate MUST still require at least one requested module to have
  a `tests/` directory before it fires (see REQ-QAJ-002 and REQ-QAJ-003)

### Requirement: REQ-QAJ-006 — Colors preserved and no staircase effect via a pty

When `oe -Q` runs, the Odoo log MUST be streamed to the console preserving ANSI
colors AND MUST NOT exhibit the staircase effect (the rightward cascade caused by
`docker -t` output captured through a plain PIPE, where `\n` lacks `\r`).

To satisfy both guarantees simultaneously, `QaCommand` MUST execute the docker
command through a **pseudo-terminal (pty)**:

- **Layer 1** — docker's stdout is a real terminal, giving correct line discipline
  (ONLCR) so no staircase occurs.
- **Layer 2** — the `-t` tty flag lets Odoo inside the container see a tty, so ANSI
  colors are preserved.

The pty master fd MUST be read line-by-line; each line MUST be reprinted to the
console with colors intact and MUST also be fed to the failure and count parsers.

#### Scenario: Colors are preserved on the console

- GIVEN `oe -Q my_module` runs with a tty-enabled docker command
- WHEN Odoo emits ANSI-colored log lines
- THEN the lines MUST be reprinted to the console with their ANSI color sequences
  intact

#### Scenario: No staircase effect in the streamed output

- GIVEN `oe -Q my_module` runs through a pty
- WHEN the pty master fd is read and reprinted line-by-line
- THEN the reprinted output MUST NOT cascade rightward (no staircase effect)
- AND line breaks MUST be rendered as proper newlines

#### Scenario: The visual guarantees are validated by a real run plus mocked-pty unit tests

- GIVEN the staircase effect is not fully unit-testable without a real docker run
- WHEN the change is verified
- THEN the color and no-staircase guarantees MUST be validated by a manual real-run
  check AND by mocked-pty unit tests that feed synthetic Odoo lines and assert the
  read/reprint loop preserves the bytes as emitted

### Requirement: REQ-QAJ-007 — Output is streamed live, line by line

`oe -Q` MUST stream Odoo's output line-by-line in real time. The output MUST NOT be
buffered until the process exits: each line MUST be reprinted to the console as soon
as it is read from the pty master fd, so a developer sees the log while a `wdb`
breakpoint is active (or while the run is still in progress).

#### Scenario: Lines appear before the process exits

- GIVEN `oe -Q my_module` is running and a `wdb` breakpoint is active
- WHEN Odoo emits log lines during the run
- THEN each line MUST be reprinted to the console as it is read
- AND the developer MUST see the log while the process is still running
- AND the output MUST NOT be withheld until the process terminates

## Non-Requirements (explicitly out of scope)

The following behaviors are intentionally NOT specified and MUST NOT be implemented
in this change:

- **Per-module verb selection (`-i` vs `-u`).** Part A's verb selection is already
  specified in the archived `qa-verb` domain (`openspec/specs/qa-verb/spec.md`) and
  is unchanged by this change.
- **Merging the `oe -Q` executor with the CI runner.** `odoo_env/qa/runner.py`
  (`TestRunner`) keeps its own execution model. The two executors share only the
  detectors `is_error_line` and `parse_test_count`.
- **Coverage / threshold handling.** Coverage and threshold decisions remain the
  CI path's responsibility and are not introduced to `oe -Q`.
