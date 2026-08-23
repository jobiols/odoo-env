# Tasks: qa-zero-tests-error (Part B)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 420–520 additions + ~15 deletions |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

```text
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium
```

> **Forecast note (honest):** the dominant cost is new test code, not production code.
> `parse_test_count` + `QaCommand` (enum, seam, judge, execute) + threading add ~230–280
> production lines; the synthetic-line unit tests add ~190–240 lines. The budget is 600, so a
> single PR fits, but this approaches the 400-line review comfort zone. One manual step exists
> (REQ-QAJ-006 colors/no-staircase) that **cannot** be unit-tested without a real Docker run.

**Strict TDD mode:** active. Test runner: `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`.
Sequence RED (failing test) → GREEN (minimal implementation) → TRIANGULATE (extra cases) → REFACTOR.

**Scope guard (non-goals):** do NOT modify per-module verb selection (`-i` vs `-u`, Part A);
do NOT merge `QaCommand` with `odoo_env/qa/runner.py::TestRunner` (CI path); do NOT add coverage.
`is_error_line` is reused unchanged.

---

## Phase 1 — Infrastructure (parser + verdict enum)

- [x] **1.1 (RED)** Add failing `parse_test_count` unit tests

- File: `odoo_env/test_qa.py` (co-located with existing `FailureDetectionTests`, which already
  cover `odoo_env/qa/failures.py`).
- Add class `ParseTestCountTests(unittest.TestCase)` covering:
  - `parse_test_count("0 failed, 0 error(s) of 5 tests") == 5`
  - `parse_test_count("0 failed, 0 error(s) of 0 tests") == 0`
  - `parse_test_count("INFO: Modules loaded.") is None`
  - ANSI-wrapped summary `"\x1b[32m0 failed, 0 error(s) of 7 tests\x1b[0m"` returns `7`
- Verify RED: `PYTHONPATH=. python3 -m unittest odoo_env.test_qa.ParseTestCountTests` fails with `ImportError`/`AttributeError`.

- [x] **1.2 (GREEN)** Implement `parse_test_count` in `odoo_env/qa/failures.py`

- Add module-level `TEST_COUNT_PATTERN = re.compile(r"of (\d+) tests")`.
- Add `def parse_test_count(line: str) -> int | None:` — `strip_ansi(line)` then `search`;
  return `int(m.group(1))` on match else `None`. Reuse existing `strip_ansi`, never return `0` for non-matches.
- Verify GREEN: `PYTHONPATH=. python3 -m unittest odoo_env.test_qa.ParseTestCountTests` passes.

- [x] **1.3 (RED)** Add `QaVerdict` enum + `QaCommand` constructor contract test

- File: `odoo_env/test_create_test_db.py` (import `QaVerdict`, `QaCommand` from `odoo_env.command`).
- Add minimal contract test asserting:
  - `QaVerdict` has exactly `PASS`, `FAIL_LINE`, `ZERO_TESTS`.
  - `QaCommand(parent, command=["docker","..."], usr_msg="x", any_requested_has_tests=True)`
    is a `Command` subclass and stores the flag + `_exit_code is None`.
- Verify RED: `PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db` fails (missing symbols).

- [x] **1.4 (GREEN)** Add `QaVerdict` enum and `QaCommand` skeleton in `odoo_env/command.py`

- Add `from enum import Enum, auto`, plus imports for `os`, `pty`, `sys`, and
  `from odoo_env.qa.failures import is_error_line, parse_test_count` (used later).
- Define `class QaVerdict(Enum): PASS = auto(); FAIL_LINE = auto(); ZERO_TESTS = auto()`.
- Define `class QaCommand(Command)` with `__init__(self, parent, command, usr_msg, any_requested_has_tests)`
  calling `super().__init__(parent, command=command, usr_msg=usr_msg)`, storing
  `self._any_requested_has_tests` and `self._exit_code: int | None = None`.
  Stub `execute()`, `_stream_lines()`, `_judge_stream()` (raise `NotImplementedError`) for now.
- Verify GREEN: 1.3 contract test passes.

---

## Phase 2 — Implementation (QaCommand behaviour + threading)

- [x] **2.1 (RED)** Add `_judge_stream` unit tests (pure decision logic)

- File: `odoo_env/test_create_test_db.py`, class `TestJudgeStream(unittest.TestCase)`.
- Use synthetic line lists + `any_has_tests` flag; capture stdout (`contextlib.redirect_stdout` /
  patched `sys.stdout` with `io.StringIO`) to assert reprint+flush. Cover:
  - PASS: `["INFO: loading", "0 failed, 0 error(s) of 5 tests"]`, any_has_tests=True → `PASS`.
  - FAIL_LINE: a line containing `: FAIL: TestX.test_y` → `FAIL_LINE` (even with a later summary line).
  - ZERO_TESTS: `["0 failed, 0 error(s) of 0 tests"]`, any_has_tests=True → `ZERO_TESTS`.
  - No-tests-dir pass: `of 0 tests` + any_has_tests=False → `PASS`.
  - Aggregation: `["... of 2 tests", "... of 3 tests"]`, any_has_tests=True → `PASS` (aggregate 5, not 0).
  - ANSI failure line still → `FAIL_LINE`; reprinted line keeps raw ANSI bytes.
- Verify RED: `PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestJudgeStream` fails (stub raises).

- [x] **2.2 (GREEN)** Implement `_judge_stream(self, lines, any_has_tests) -> QaVerdict`

- Iterate `lines`; for each line reprint verbatim with flush (colors intact, no ANSI strip on
  the printed copy); run `is_error_line(line)` and accumulate `parse_test_count(line)`.
- Return `FAIL_LINE` if any failure line; else `ZERO_TESTS` if aggregate == 0 and `any_has_tests`;
  else `PASS`. Do NOT inspect exit code here (that is `execute()`'s job).
- Verify GREEN: `TestJudgeStream` passes.

- [x] **2.3 (RED)** Add mocked PTY-seam tests for `_stream_lines`

- File: `odoo_env/test_create_test_db.py`, class `TestPtySeam(unittest.TestCase)`.
- Monkeypatch the pty/I/O internals (no real pty, no Docker). Cover:
  - EIO on child exit is treated as EOF (no exception).
  - Partial-line buffering: two `os.read` chunks split mid-line are reassembled and yielded whole.
  - `errors="replace"` decode path (invalid UTF-8 bytes do not raise).
  - Exit code is captured onto `self._exit_code` after the loop.
- Verify RED: `PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestPtySeam` fails (stub).

- [x] **2.4 (GREEN)** Implement `_stream_lines(self, cmd) -> Iterator[str]` (PTY seam)

- Implement the ADR-2 loop exactly: `pty.openpty()`; `Popen(cmd, stdout=slave, stderr=slave, close_fds=True)`;
  `os.close(slave)` in parent; `os.read(master, 4096)` loop; `except OSError` (EIO on child exit) → EOF;
  buffer bytes, split on `b"\n"`, yield `decode("utf-8", errors="replace")`; yield final partial line;
  `process.wait()`; set `self._exit_code = process.returncode`; `finally: os.close(master)`.
- Keep this method the ONLY pty/`os.read`/`Popen` surface so tests override it cleanly.
- Verify GREEN: `TestPtySeam` passes.

- [x] **2.5 (GREEN)** Implement `execute()` orchestration in `QaCommand`

- `lines = self._stream_lines(self.command)` → `verdict = self._judge_stream(lines, self._any_requested_has_tests)`.
- Apply ADR-3 decision order and abort via `msg.err(...)` (which raises `OeError`):
  1. `verdict is FAIL_LINE` → `msg.err("Test failure detected")`.
  2. `self._exit_code != 0` → `msg.err(f"Odoo exited with code {self._exit_code}")`.
  3. `verdict is ZERO_TESTS` → `msg.err("0 tests collected ...")` (explicit zero-tests message per issue #128).
  4. else → success (no-op).
- Add a test to `TestPtySeam`/`TestJudgeStream` that overrides `_stream_lines` with canned lines +
  a fake exit code and asserts `execute()` raises `OeError` on FAIL/ZERO_TESTS/nonzero exit, and does
  not raise on PASS.
- Verify: `PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db` passes.

- [x] **2.6 (GREEN)** Update `EnvironmentManager.qa()` in `odoo_env/managers/environment_manager.py`

- Change signature to `qa(self, database, install_modules, update_modules, *, any_requested_has_tests: bool = False) -> list[Command]`.
- In the `RunSpec`, set `interactive=True` and `tty=True` unconditionally (drop `tty = sys.stdin.isatty()`).
- Build `QaCommand(parent, command=cmd_list, usr_msg=step_msg, any_requested_has_tests=any_requested_has_tests)`
  instead of plain `Command`.
- Verify: existing command-composition tests (`test_create_test_db.py` REQ-QAV tests) still pass;
  `TestModuleCommandTty` in `test_environment_manager.py` will need the update in 3.4.

- [x] **2.7 (GREEN)** Update `OdooEnv.qa()` in `odoo_env/odooenv.py`

- After module resolution/partition, compute:
  `testable = [m for m in modules_list if (Path(self.client.custom_modules_dir) / m / "tests").is_dir()]`
  then `any_requested_has_tests = bool(testable)`.
- Pass `any_requested_has_tests=any_requested_has_tests` to `EnvironmentManager(...).qa(database, install_modules, update_modules, ...)`.
- Keep Part A partition logic and all existing guards unchanged.
- Verify: `test_oe.py::test_qa` still passes (command list unchanged; now returns `QaCommand`).

---

## Phase 3 — Testing (coverage, regression, manual)

- [x] **3.1 (TRIANGULATE)** Complete `_judge_stream` + `parse_test_count` edge cases

- Add remaining spec scenarios to `TestJudgeStream` / `ParseTestCountTests`:
  - multi-summary `-i`+`-u` aggregation equals the SUM (not last value), per REQ-QAJ-005.
  - failure gate fires BEFORE zero-tests when both a `: FAIL:` line and `of 0 tests` appear.
  - unrelated text (`bad query:`, `violates unique constraint`) is NOT a failure line.
  - no summary line at all + any_has_tests=True → ZERO_TESTS (aggregate stays 0), per REQ-QAJ-005.
- Verify: `PYTHONPATH=. python3 -m unittest odoo_env.test_qa odoo_env.test_create_test_db`.

- [x] **3.2** Threading tests for `any_requested_has_tests`

- File: `odoo_env/test_create_test_db.py`, class `TestAnyRequestedHasTests`.
- Use mocked `custom_modules_dir` / `discover_modules_in` + `Path.is_dir` to assert:
  - module with a `tests/` subdir sets the flag True.
  - module without a `tests/` subdir sets the flag False.
  - `OdooEnv.qa()` threads the flag into the returned `QaCommand` (assert `cmd._any_requested_has_tests`).
  - `EnvironmentManager.qa()` returns a `QaCommand` (not a plain `Command`) with the flag stored.
- Verify: `PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestAnyRequestedHasTests`.

- [x] **3.3** Update existing tests affected by the `qa()` change

- `odoo_env/test_environment_manager.py::TestModuleCommandTty::test_qa_omits_it_when_no_tty` —
  ADR-6 makes `qa()` always `tty=True`; rewrite/rename to assert `-it` is ALWAYS present regardless
  of `sys.stdin.isatty()`. Keep `_build_module_command` tty tests (unchanged behaviour) as-is.
- `odoo_env/test_create_test_db.py::TestQaCli` — confirm `qa()` return type is `QaCommand`; update
  `_build_qa_command`/command-composition tests if they assert `type(...) is Command`.
- `odoo_env/test_oe.py::test_qa` — confirm still passes (command list is byte-identical; `-it` already present).
- Verify full suite: `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`.

- [x] **3.4** Document + perform MANUAL real-run verification (REQ-QAJ-006)

- Not unit-testable without Docker. Add a short manual checklist (in the PR description or a code comment
  near `_stream_lines`): run `oe -Q <module_with_colored_failing_test>` and confirm (a) ANSI colors are
  preserved on the console, and (b) no staircase/rightward cascade appears.
- This manual step MUST be completed before merge; record the result in the PR.
- No automated test is added for color/staircase beyond the mocked-pty loop tests from 2.3.

- [x] **3.5** Final full-suite verification

- Run `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`; confirm zero failures.
- Confirm no drift from the spec: every REQ-QAJ-001..007 scenario has a corresponding test or the
  documented manual verification.
