# Apply Progress: qa-zero-tests-error (Part B)

First apply batch. All 16 implementation tasks (1.1 → 3.5) completed. Strict TDD
(RED → GREEN → TRIANGULATE → REFACTOR) followed throughout.

## Summary

Turned `oe -Q` into a real QA gate by adding a PTY-streaming `QaCommand` that
reuses the proven `is_error_line` detector and a new `parse_test_count` parser,
then aborts on a failure line, a non-zero exit, or a zero-tests condition (when
at least one requested module has a `tests/` directory). Part A verb selection
(`-i`/`-u`) is unchanged; the CI `TestRunner` is untouched.

## Baseline vs final test count

- Baseline (before any edit): **279 tests, OK**
- Final (full suite): **306 tests, OK**
- Delta: **+27 tests** (all new Part B coverage; no pre-existing test removed/broken)

Test command (both runs):
`PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"`

## Changed-line count

`git diff --stat` (working tree) totals `479 insertions(+), 18 deletions(-)`.
That includes a **pre-existing** `openspec/config.yaml` edit (2+/2-) that was
already present before this batch (venv → `python3` in the test command) and was
NOT authored here. Excluding that pre-existing edit, this batch changed:

- `odoo_env/command.py` (+117)
- `odoo_env/managers/environment_manager.py` (+23/-5)
- `odoo_env/odooenv.py` (+18/-2)
- `odoo_env/qa/failures.py` (+21)
- `odoo_env/test_create_test_db.py` (+262)
- `odoo_env/test_environment_manager.py` (+10/-9)
- `odoo_env/test_qa.py` (+26)

**This batch: 477 insertions + 16 deletions = 493 changed lines.** Within the
420–520 forecast; single PR, no size exception needed.

## Tasks completed (all checkboxes now `- [x]`)

| Task | Status | Notes |
|------|--------|-------|
| 1.1 (RED) `parse_test_count` tests | done | `ParseTestCountTests` in `test_qa.py` |
| 1.2 (GREEN) `parse_test_count` impl | done | `TEST_COUNT_PATTERN` + fn in `qa/failures.py` |
| 1.3 (RED) `QaVerdict`/`QaCommand` contract test | done | `TestQaCommandContract` |
| 1.4 (GREEN) `QaVerdict` + `QaCommand` skeleton | done | enum + class in `command.py` |
| 2.1 (RED) `_judge_stream` tests | done | `TestJudgeStream` |
| 2.2 (GREEN) `_judge_stream` impl | done | pure decision logic |
| 2.3 (RED) mocked PTY-seam tests | done | `TestPtySeam` |
| 2.4 (GREEN) `_stream_lines` impl | done | pty/os.read/Popen seam |
| 2.5 (GREEN) `execute()` orchestration | done | `TestQaCommandExecute` |
| 2.6 (GREEN) `EnvironmentManager.qa()` | done | returns `QaCommand`, always `-it` |
| 2.7 (GREEN) `OdooEnv.qa()` | done | threads `any_requested_has_tests` |
| 3.1 (TRIANGULATE) edge cases | done | failure-before-zero, unrelated text, no-summary |
| 3.2 threading tests | done | `TestAnyRequestedHasTests` |
| 3.3 update affected tests | done | tty test + `_fake_client` |
| 3.4 manual real-run note | done-with-manual-note | checklist in `_stream_lines` docstring |
| 3.5 final full-suite | done | 306 OK |

## TDD Cycle Evidence (strict TDD active)

| # | Phase | RED evidence | GREEN evidence |
|---|-------|--------------|----------------|
| 1 | `parse_test_count` | `unittest odoo_env.test_qa.ParseTestCountTests` → 4× `AttributeError: ... has no attribute 'parse_test_count'` | 4/4 OK |
| 2 | `QaVerdict`/`QaCommand` skeleton | `TestQaCommandContract` → `ImportError: cannot import name 'QaCommand'` | 2/2 OK |
| 3 | `_judge_stream` | `TestJudgeStream` → 6× `NotImplementedError` | 6/6 OK |
| 4 | `_stream_lines` | `TestPtySeam` → 4× `NotImplementedError` | 4/4 OK |
| 5 | `execute()` | `TestQaCommandExecute` → 4× `NotImplementedError` | 4/4 OK |
| 6 | TRIANGULATE `_judge_stream` edge cases | (already-green code; added 3 scenarios) | 9/9 OK |
| 7 | threading | (green code; added 4 scenarios) | 4/4 OK |
| 8 | existing-test updates | `test_qa_omits_it_when_no_tty` rewritten → `test_qa_always_uses_it_even_when_no_tty` | full suite OK |

## Files changed

- `odoo_env/command.py` — `QaVerdict`, `QaCommand` (enum + PTY `execute`/`_stream_lines`/`_judge_stream`).
- `odoo_env/qa/failures.py` — `TEST_COUNT_PATTERN` + `parse_test_count` (reuses `strip_ansi`).
- `odoo_env/managers/environment_manager.py` — `qa()` returns `QaCommand`, `interactive=True`/`tty=True` unconditionally.
- `odoo_env/odooenv.py` — `qa()` computes `any_requested_has_tests` and threads it down.
- `odoo_env/test_create_test_db.py` — `TestQaCommandContract`, `TestJudgeStream`, `TestPtySeam`, `TestQaCommandExecute`, `TestAnyRequestedHasTests`.
- `odoo_env/test_environment_manager.py` — tty test for `qa()` updated to assert `-it` always present.
- `odoo_env/test_qa.py` — `ParseTestCountTests`; `_fake_client` gained `custom_modules_dir`.

## Deviations from design

1. **`sys` not imported in `command.py`** — the task/design text listed it, but the PTY loop only needs `pty`/`os`/`subprocess`; adding `sys` would be an unused import.
2. **Manual checklist placement** — documented in the `_stream_lines` docstring (near the seam) rather than a PR description, per the orchestrator instruction.
3. **`test_qa.py::_fake_client`** — added `custom_modules_dir` because `OdooEnv.qa()` now reads it (previously that test never touched it). Harmless for other `_fake_client` consumers.
4. **`openspec/config.yaml`** — NOT modified by this batch; the `venv`→`python3` edit was already staged in the working tree before apply started.

Decision order implemented exactly as ADR-3 / gotcha requires: FAIL_LINE → non-zero
exit → ZERO_TESTS → success, so the first `msg.err` aborts.

## Remaining tasks (exact unchecked lines)

None — all 16 task checkboxes are `- [x]`.

## Deferred to the user (before merge)

- **REQ-QAJ-006 manual real-run** (task 3.4): run `oe -Q <module_with_colored_failing_test>`
  in a real Docker environment and confirm (a) ANSI colors preserved, (b) no staircase
  cascade. This cannot be unit-tested (no Docker/real pty in tests). Checklist is recorded
  in the `_stream_lines` docstring.

## Workload / PR boundary

Single PR. 493 changed lines (477+ / 16-), within the 420–520 forecast and under the
800-line session review budget. `Decision needed before apply: No`, `Chained PRs
recommended: No`.

## Structured status consumed

- Native SDD status: `change=qa-zero-tests-error`, `artifactStore=openspec`,
  `applyState=ready`, `nextRecommended=apply`, `blockedReasons=[]`.
- `workspaceRoot / allowedEditRoots`: `/home/jobiols/tmp/odoo-env` (whole repo editable).
- `actionContext`: no warnings; no edit-root violations.

## Verification commands run

```bash
PYTHONPATH=. python3 -m unittest odoo_env.test_qa.ParseTestCountTests
PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestQaCommandContract
PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestJudgeStream
PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestPtySeam
PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestQaCommandExecute
PYTHONPATH=. python3 -m unittest odoo_env.test_create_test_db.TestAnyRequestedHasTests
PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"   # final: 306 OK
```
