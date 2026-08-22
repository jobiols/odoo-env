# Apply Progress: QA Verb Selection by Module State (Part A)

Change ID: `qa-verb-by-module-state`
Artifact store: OpenSpec
Batch: first (and only) batch — implementation complete.

## Structured Status Consumed

- `schemaName`: spec-driven
- `artifactStore`: openspec (authoritative; `openspec/` directory present)
- `applyState`: ready (all tasks were unchecked at start)
- `actionContext`: repo-local; edits confined to `odoo_env/` and `openspec/changes/qa-verb-by-module-state/` under the authoritative workspace `/home/jobiols/tmp/odoo-env`.
- `dependencies.apply`: ready (spec, design, tasks all read in full).

## Review Workload Gate

- `Decision needed before apply`: No
- `Chained PRs recommended`: No
- `Chain strategy`: pending (no chaining)
- `400-line budget risk`: Medium
- Resolved delivery: single-pr, review budget 600 lines. Forecast ≈350–420 changed lines (mostly tests).

## Completed Tasks

All 13 implementation-owned task boxes are checked `[x]` in `openspec/changes/qa-verb-by-module-state/tasks.md`:

1.1, 1.2, 2.1.1, 2.1.2, 2.2.1, 2.2.2, 2.3.1, 2.3.2, 3.1, 3.2, 4.1, 4.2, 4.3.

No `sdd-owner` markers present — all rows are legacy implementation-owned. No parent-owned rows deferred.

## Files Changed

- `odoo_env/odooenv.py`
  - ADD `OdooEnv._installed_modules(database: str) -> set[str]` (safe `docker exec` psql, fixed SQL, argv list, no shell, `capture_output=True, text=True, check=False`, empty set on non-zero returncode).
  - MODIFY `OdooEnv.qa(self, modules_to_test)`: database resolution → on-disk guard (skip for "all") → DB-exists guard → state query → Python partition → delegate with two lists.
- `odoo_env/managers/environment_manager.py`
  - MODIFY `EnvironmentManager.qa(self, database, install_modules, update_modules)`: conditional `-i`/`-u`, preserved all existing `RunSpec` settings, `step_msg` joins both partitions.
- `odoo_env/test_create_test_db.py`
  - ADD 16 new tests under `TestQaCli` (`_installed_modules`, command composition, guards, partitioning, triangulation/determinism).
  - MODIFY 2 existing tests (`test_qa_passes_full_module_name`, `test_qa_all_expands_to_discovered_testable_modules`) to mock `_db_exists` / `discover_modules_in` / `_installed_modules`.
- `odoo_env/test_environment_manager.py`
  - MODIFY 2 existing TTY tests to the new `EnvironmentManager.qa()` signature.
- `odoo_env/test_oe.py`
  - MODIFY `TestRepository.test_qa` to mock the new guard flow (preserving the full-command `-u` assertion).
- `odoo_env/test_qa.py`
  - MODIFY `OeIntegrationTests.test_dash_q_uses_original_qa_method` to the string `modules_to_test` and mock the new guard flow.

Note: `docs/_config.yml` was already modified in the working tree before this work; it was not touched by this change.

## Test Command

Corrected runner (venv path in `openspec/config.yaml` does not exist; system `python3` is Python 3.12.3):

```bash
PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"
```

Baseline (before any change): **261 tests, OK**.

Final (after implementation): **279 tests, OK** (+18 new tests, 0 regressions).

The literal `FAILED: mod_a` and `FAIL: TestXxx.test_x` lines in output are code-under-test stdout, not unittest failures — trusted only the final `OK`/`FAILED` summary line.

## TDD Cycle Evidence (Strict TDD)

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|-----------|-----|-------|-------------|----------|
| 2.1 `_installed_modules` | `test_create_test_db.py` | Unit | ✅ 261/261 | ✅ 3 errors `AttributeError: no attribute _installed_modules` | ✅ 3/3 OK | ✅ fixed-SQL + no-`IN` test | ➖ clean |
| 2.2 `EnvironmentManager.qa` | `test_create_test_db.py` | Unit | ✅ 261/261 | ✅ 4 errors `TypeError: takes 3 positional args but 4 given` | ✅ 4/4 OK | ✅ empty-verb omit + single-command | ✅ `step_msg` join |
| 2.3 `OdooEnv.qa` | `test_create_test_db.py` | Unit | ✅ 261/261 | ✅ 10 errors + 1 failure (old `qa` signature/flow) | ✅ 9/9 OK | ✅ sorted partitions | ✅ none needed |
| 4.1 existing-test updates | `test_create_test_db.py` | Unit | ✅ 261/261 | ✅ (broken by signature change) | ✅ green | ➖ single | ➖ none |
| 4.2/4.3 full suite + cross-check | all `test_*.py` | Unit | ✅ 261/261 | N/A | ✅ 279/279 OK | ✅ REQ-QAV-001..006 mapped | ✅ none |

Representative RED evidence (2.1): `AttributeError: 'OdooEnv' object has no attribute '_installed_modules'`.
Representative RED evidence (2.2/2.3): `TypeError: EnvironmentManager.qa() missing 1 required positional argument: 'update_modules'`.
Representative GREEN evidence: `Ran 279 tests ... OK`.

## Test Summary

- Total new tests written: 18
- Total tests passing: 279 (261 pre-existing + 18 new)
- Layers used: Unit (279)
- Approval tests (refactoring): 0 — no production refactor of existing behavior; only additive/extended methods
- Pure functions created: `_installed_modules` (side-effect-free query), plus Python set partitioning inline

## REQ-QAV Cross-Check (step 4.3)

| Requirement | Passing test(s) |
|-------------|-----------------|
| REQ-QAV-001 not-installed → `-i` | `test_qa_all_new_modules_use_install_verb`, `test_qa_command_omits_empty_verbs`, `test_qa_mixed_modules_produce_dual_verb_command` |
| REQ-QAV-002 installed → `-u` | `test_qa_all_installed_modules_use_update_verb`, `test_qa_passes_full_module_name`, `test_qa_all_expands_to_discovered_testable_modules` |
| REQ-QAV-003 mixed → single dual-verb | `test_qa_mixed_modules_produce_dual_verb_command`, `test_qa_single_command_for_mixed_modules`, `test_qa_command_omits_empty_verbs` |
| REQ-QAV-004 safe psql + Python partition | `test_installed_modules_uses_correct_psql_command`, `test_installed_modules_parses_psql_output`, `test_installed_modules_returns_empty_on_error`, `test_installed_modules_sql_is_fixed_without_interpolation`, `test_qa_partitions_modules_by_install_state` |
| REQ-QAV-005 missing test DB aborts | `test_qa_aborts_when_test_db_missing`, `test_qa_db_error_suggests_create_test_db` |
| REQ-QAV-006 unknown module aborts | `test_qa_aborts_on_unknown_module`, `test_qa_aborts_lists_all_unknown_modules` |

No gaps. Part B and the CI path (`odoo_env/qa/runner.py`) were intentionally left untouched per spec Non-Requirements.

## Deviations from Design

- None material. The only implementation detail note: `EnvironmentManager.qa()` now uses `list[str]` type annotations (Python ≥3.9, consistent with the project floor). `step_msg` phrasing is "Performing tests on module(s) {join}" (design's exact wording), preserving all `RunSpec` invariants from ADR-5.

## Remaining Tasks

None. All 13 implementation tasks complete and checked in `tasks.md`.

## Next Recommended

`parent-lifecycle` — implementation is complete; do not start verify/bounded-review from this phase.
