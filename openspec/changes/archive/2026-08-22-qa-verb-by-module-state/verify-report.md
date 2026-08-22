```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:1b13c8029093353c69322e078f5d4023540cc4852d4466b61fe1600814d63df5
verdict: pass
blockers: 0
critical_findings: 0
requirements: 6/6
scenarios: 13/13
test_command: PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"
test_exit_code: 0
test_output_hash: sha256:5a8dfa372460e8b560efc3a09379cef49e5e88e3a8457573e87bb0ce219bb211
build_command: python3 -m compileall -q odoo_env
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

# Verify Report: QA Verb Selection by Module State (Part A)

Change ID: `qa-verb-by-module-state`
Resolves: GitHub issue #128 (Part A)
Artifact store: OpenSpec (authoritative)

## Status

**PASS** — no CRITICAL or WARNING findings. Three SUGGESTION-level observations
noted at the end (none block archive).

## Structured Status / ActionContext Findings

- `schemaName`: spec-driven
- `artifactStore`: openspec (authoritative; `openspec/` directory present, config read)
- `actionContext`: repo-local. All source edits confined to `odoo_env/` under the
  authoritative workspace `/home/jobiols/tmp/odoo-env`.
- `dependencies.verify`: spec, tasks, apply-progress all read in full and consistent.
- No `blockedReasons`. No edit-authority concern (implementation already committed).

## Spec Coverage (REQ-QAV-001 .. REQ-QAV-006)

Every requirement scenario is implemented in source and backed by a passing test.

| Requirement | Verdict | Implementation evidence | Passing test(s) |
|-------------|---------|------------------------|-----------------|
| REQ-QAV-001 not-installed → `-i` | ✅ | `OdooEnv.qa()` partitions `requested - installed` → `install_modules`; `EnvironmentManager.qa()` emits `-i <mods>`; `--test-enable`/`--log-level=test`/`--stop-after-init` always emitted via `RunSpec` | `test_qa_all_new_modules_use_install_verb`, `test_qa_mixed_modules_produce_dual_verb_command`, `test_qa_command_omits_empty_verbs` |
| REQ-QAV-002 installed → `-u` | ✅ | `requested & installed` → `update_modules`; emits `-u <mods>` | `test_qa_all_installed_modules_use_update_verb`, `test_qa_passes_full_module_name`, `test_qa_all_expands_to_discovered_testable_modules`, `test_oe.py::test_qa` (full-command `-u`) |
| REQ-QAV-003 mixed → single dual-verb | ✅ | single `extra_args` list; both `-i`/`-u` extend when non-empty; empty partition omits verb; one `Command` returned | `test_qa_mixed_modules_produce_dual_verb_command`, `test_qa_single_command_for_mixed_modules`, `test_qa_command_omits_empty_verbs` |
| REQ-QAV-004 safe psql + Python partition | ✅ | `_installed_modules()` uses argv list, `check=False`, fixed SQL `SELECT name FROM ir_module_module WHERE state = 'installed'`; no module name in argv/SQL; no `IN (...)`; partition in Python | `test_installed_modules_uses_correct_psql_command`, `test_installed_modules_sql_is_fixed_without_interpolation`, `test_installed_modules_parses_psql_output`, `test_installed_modules_returns_empty_on_error`, `test_qa_partitions_modules_by_install_state` |
| REQ-QAV-005 missing test DB aborts | ✅ | `if not self._db_exists(database): msg.err(..., --create-test-db)` before state query; `_installed_modules` not reached | `test_qa_aborts_when_test_db_missing`, `test_qa_db_error_suggests_create_test_db` |
| REQ-QAV-006 unknown module aborts | ✅ | on-disk guard via `discover_modules_in`; `msg.err("Module(s) not found on disk: ...")` | `test_qa_aborts_on_unknown_module`, `test_qa_aborts_lists_all_unknown_modules` |

Non-Requirements honored: Part B (`0 tests` ERROR detection) and the CI path
(`odoo_env/qa/runner.py`) were NOT touched. `git diff --name-only` confirms
`odoo_env/qa/runner.py` is absent from the change. `oe -Q all` discovery semantics
unchanged (delegated to `TestRunner.discover_test_modules()`).

## Task Completion Status

All 13 implementation-owned task boxes are checked `[x]`. A scan for unchecked
`- [ ]` implementation markers returned **none**. No archive blockers.

## Test / Validation Commands

Spec-declared venv path does not exist (`/home/jobiols/tmp/odoo-env/venv` absent);
used the corrected system-python runner per orchestrator context:

```bash
PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"
```

Result:

```
Ran 279 tests in 0.167s

OK
```

- Baseline (before change): 261 tests OK.
- After change: **279 tests OK, 0 regressions** (+18 new tests).
- The literal `FAILED: mod_a` / `FAIL: TestXxx.test_x` lines are code-under-test
  stdout, not unittest failures; only the final `OK` summary was trusted.

## Strict TDD Compliance

- `openspec/config.yaml` declares `strict_tdd: true`.
- `apply-progress.md` contains a `TDD Cycle Evidence` table with RED / GREEN /
  TRIANGULATE / REFACTOR columns per task (2.1, 2.2, 2.3, 4.1, 4.2/4.3) and
  representative RED/GREEN evidence strings.
- Reported test files cross-check against the codebase: all named tests exist in
  `odoo_env/test_create_test_db.py` under `TestQaCli`; signature-change updates in
  `test_environment_manager.py`, `test_oe.py`, `test_qa.py` were verified present.
- GREEN confirmed by the full-suite run above (279/279).

### Assertion Quality Audit

- No tautologies: every test asserts a concrete expected value (exact argv list,
  exact SQL string, partition lists, `-i`/`-u` token presence/absence).
- No ghost loops; no type-only assertions; no smoke-only tests.
- No implementation-detail CSS assertions (N/A — Python CLI, no CSS).
- The no-interpolation guarantee is triangulated beyond argv shape by
  `test_installed_modules_sql_is_fixed_without_interpolation` (exact fixed string,
  no `IN (`, no module name anywhere in joined argv).
- Determinism locked by `test_qa_partitions_are_sorted_for_stable_output`.

## Review Workload / PR Boundary

- Forecast: single PR, `Chained PRs recommended: No`, `400-line budget risk: Medium`,
  `Decision needed before apply: No`.
- Actual: one commit (`1aad9f1`) on `master`. No chaining. Source footprint ≈
  `odooenv.py` +70/-, `environment_manager.py` +13/-, tests +330 — consistent with
  the ≈350–420 changed-line forecast; no `size:exception` was needed.
- No scope creep into Part B or the CI path. Assigned slice only.

## Findings (non-blocking)

- **SUGGESTION** — `--stop-after-init` has no dedicated assertion in the `TestQaCli`
  command-composition tests. It is covered indirectly by `test_oe.py::test_qa`
  (full-command assertion) and by `_find_qa_run_cmd` (uses `--stop-after-init` as a
  fallback discriminator). A one-line `assertIn("--stop-after-init", cmd)` in
  `test_qa_command_contains_test_enable` would make REQ-QAV-001/002's "MUST include
  --stop-after-init" clause locally explicit.
- **SUGGESTION** — Commit `1aad9f1` also carries `docs/_config.yml` (YAML
  re-indentation) and `doc/uml/*.plantuml` (pyreverse pre-commit auto-generation)
  which are outside the declared `odoo_env/` source scope. Harmless (formatter
  output), but `apply-progress.md` states `docs/_config.yml` was pre-existing and
  untouched, which is inconsistent with it appearing in this commit's diff.
- **SUGGESTION** — `apply-progress.md` TDD evidence for task 2.3 records "10 errors +
  1 failure", while `tasks.md` 2.3.1 enumerates 9 new tests. Minor count mismatch in
  the RED-evidence narrative; does not affect the GREEN outcome.

## Exact Blockers

None.
