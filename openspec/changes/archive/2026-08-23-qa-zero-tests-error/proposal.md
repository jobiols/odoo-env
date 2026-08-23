# Proposal: qa-zero-tests-error

Part B of GitHub issue #128. Part A (`qa-verb-by-module-state`, DONE/archived) fixed
per-module verb selection (`-i` vs `-u`). Part B makes `oe -Q` actually *judge* the
test run instead of trusting Odoo's exit code.

## Intent

Turn `oe -Q` into a real QA gate. Today `oe -Q` runs a plain `Command`
(`odoo_env/command.py`) whose `execute()` calls `subprocess_call(check=True)`: it
streams Odoo's output to the console but **parses nothing**. Odoo exits with code `0`
even when:

1. **Unit tests FAIL or ERROR** — the failure is visible on screen but the command
   still "passes".
2. **Zero tests are collected** — e.g. a freshly-installed module (now installed
   thanks to Part A) whose tests are never collected, or a module with an empty
   `tests/` directory. Issue #128 explicitly calls this out: *"0 tests collected on
   a module with a tests/ dir should be an explicit ERROR, not a silent green
   WARNING."*

Both are **false greens**. The CI runner (`odoo_env/qa/runner.py::TestRunner._run_one`)
already solved case (1) with the proven `is_error_line` detector. Part B brings that
same rigor to the interactive `oe -Q` path and adds case (2).

## Scope

### In scope

1. **Detect real test failures** on the `oe -Q` path by reusing the existing,
   proven detector `odoo_env/qa/failures.py::is_error_line` (ANSI-strip + regex
   `:\s+(FAIL|ERROR): \w`) — the identical detector `TestRunner._run_one` already
   trusts. No new failure-detection logic.

2. **Detect zero tests collected** via a new small parser in
   `odoo_env/qa/failures.py`, e.g. `parse_test_count(line) -> int | None`, matching
   Odoo's summary line `of (\d+) tests`. ERROR criterion:
   - the **aggregate collected count is 0** AND
   - **at least one requested module has a `tests/` directory**.
   If no requested module has a `tests/` dir, `0 tests` is legitimate and MUST NOT
   error.

3. **New `QaCommand(Command)` subclass** in `odoo_env/command.py` whose `execute()`:
   - runs the docker command through a **pseudo-terminal (pty)**,
   - streams output live to the console (colors intact),
   - parses each line for failures (`is_error_line`) and test counts
     (`parse_test_count`),
   - aborts via `msg.err` / non-zero on a detected failure or on the zero-tests
     condition.
   This honors the config rule *"prefer extending the Command subclass pattern over
   modifying subprocess calls"*.

4. **Thread modules-with-tests into `QaCommand`**. `OdooEnv.qa()`
   (`odoo_env/odooenv.py`) computes which **requested** modules have a `tests/`
   directory (under `self.client.custom_modules_dir`; a module = subdir with
   `__manifest__.py`, a testable module additionally has a `tests/` subdir — reuse
   the spirit of `TestRunner.discover_test_modules()` but scoped to the requested
   list) and threads that fact down so the zero-tests criterion can be evaluated.

5. **Enable `-t` (tty) for the `oe -Q` docker command** on this path so Odoo inside
   the container emits colors. `RunSpec` already carries a `tty` field (added by the
   staircase fix); confirm the qa path can request `-t` here.

6. **Tests** (unittest, strict TDD): unit-test the pty execution with mocks/fakes
   (mock the pty + `Popen`), feeding synthetic Odoo output including `of 0 tests`,
   `of 5 tests`, and a `: FAIL:` line; plus the new `parse_test_count` parser and the
   `TestQaCli`-level wiring (`odoo_env/test_create_test_db.py`).

### Non-goals

- **Do NOT merge the `oe -Q` executor with the CI runner** (`odoo_env/qa/runner.py`).
  They use different command models (Command vs RunSpec-driven `TestRunner`). Reuse
  `is_error_line` and the new count parser, but keep the two executors separate.
- **No coverage / threshold handling** — that stays the CI path's responsibility.
- **Part A's verb selection (`-i`/`-u`) is unchanged.**

## Critical design constraint: colors vs the staircase effect

This is the primary risk and the reason a pty is required rather than a plain pipe.

- The user wants the Odoo log to keep **ANSI colors** on the console (easier to
  read).
- Odoo only emits colors when it sees a tty (docker `-t`).
- **But** a prior fix in this repo (commit `369a12f`, session 2026-06-15) proved that
  `docker run -t` + stdout captured by a plain `subprocess.Popen` PIPE causes the
  **staircase effect** (raw-mode output: `\n` without `\r`, so lines cascade
  rightward). That fix set `tty=False` in the CI runner to get clean output — at the
  cost of colors. Note: `text=True` universal-newline handling makes `rstrip('\r')` a
  no-op; the culprit is `-t` + pipe, not `\r`.
- **Therefore Part B uses a pty** so that:
  - **Layer 1** — docker's stdout is a *real terminal*, giving correct line
    discipline (ONLCR) → **no staircase**.
  - **Layer 2** — docker `-t` lets Odoo inside the container see a tty → **colors
    preserved**.
  We read the pty master fd line-by-line to reprint (colors intact) **and** parse.
  This is more complex and riskier than the CI runner's simple `Popen` + PIPE and
  touches the exact area of the past staircase bug.

## Affected areas

| File | Change |
|------|--------|
| `odoo_env/command.py` | New `QaCommand(Command)` subclass with pty-based `execute()` that streams + parses and aborts on failure / zero-tests. |
| `odoo_env/qa/failures.py` | Add `parse_test_count(line) -> int \| None` for `of (\d+) tests`; `is_error_line` reused unchanged. |
| `odoo_env/managers/environment_manager.py` | `qa()` returns the new `QaCommand` (carrying modules-with-tests + docker command with tty enabled for this path). |
| `odoo_env/odooenv.py` | `qa()` computes which requested modules have `tests/` and threads it down. |
| `odoo_env/services/docker_client.py` | Confirm the qa path can request `-t`; `RunSpec.tty` already exists. |
| `odoo_env/test_create_test_db.py` (`TestQaCli`) and/or a new QaCommand-focused test | Unit tests for pty execution (mocked), `parse_test_count`, and CLI wiring. |

## Risks

1. **PTY execution near the historical staircase bug (PRIMARY).** The pty read/reprint
   loop is the highest-risk element; it operates in the exact area of commit `369a12f`.
   Mitigation: mock the pty in unit tests with synthetic Odoo lines; manually verify on
   a real run that colors are preserved AND no staircase appears before merge.
2. **PTY portability / testability.** `pty` + master-fd reads are POSIX and awkward to
   unit-test. Mitigation: isolate pty setup behind a thin seam so tests mock `pty` and
   `Popen`; feed synthetic lines.
3. **False positive / false negative on zero-tests.** The `of (\d+) tests` line format
   or aggregation could misfire (e.g. multiple summary lines across `-i` and `-u`
   phases). Mitigation: aggregate counts across all summary lines; only error when
   aggregate is 0 AND a requested module has `tests/`; cover both branches in tests.
4. **`is_error_line` false positives on colored output.** Mitigation: detector already
   ANSI-strips; reuse it unchanged (no new regex for failures).
5. **Divergence between `oe -Q` and CI runner behavior.** Two executors could drift.
   Mitigation: share the detectors (`is_error_line`, `parse_test_count`) even though
   executors stay separate.

## Rollback

The change is **additive**:

- `QaCommand` is a new subclass; `qa()` can revert to returning the plain `Command`.
- The `failures.py` addition (`parse_test_count`) is isolated and side-effect free.
- Reverting `qa()` in `environment_manager.py`/`odooenv.py` restores current (Part A)
  behavior, including verb selection.

Revert restores exactly the current Part A behavior with no data or state migration.

## Success criteria

1. `oe -Q <module>` where a test FAILs/ERRORs → command aborts with `msg.err` and a
   non-zero result (no false green).
2. `oe -Q <module>` where the module has a `tests/` dir but **0 tests are collected**
   → command aborts with an explicit ERROR (per issue #128).
3. `oe -Q <module>` where **no** requested module has a `tests/` dir and 0 tests run →
   command **passes** (legitimate, not an error).
4. `oe -Q` output keeps **ANSI colors** and shows **no staircase effect**.
5. Failure detection reuses `is_error_line` unchanged; zero-tests uses the new
   `parse_test_count`.
6. `oe -Q` executor and CI runner remain separate; only detectors are shared.
7. Part A verb selection (`-i`/`-u`) behavior is unchanged.
8. All tests pass:
   `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`.

## Delivery constraints

- Project: odoo-env. Strict TDD (unittest).
- Test command: `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`.
- Delivery strategy: single-pr, review budget 600 lines.
