# Tasks: QA Verb Selection by Module State (Part A)

Change ID: `qa-verb-by-module-state`
Resolves: GitHub issue #128 (Part A)
Spec: `specs/qa-verb/spec.md` · Design: `design.md`

Implementation tasks for selecting the Odoo verb (`-i` vs `-u`) per module based on its
real install state in `<client>_test`. Strict TDD is active (unittest): every behavior
is written RED (failing test) first, then implemented GREEN, then triangulated.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ≈350–420 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending (no chaining needed) |

Rationale: two source methods touched (`odooenv.py` +~45, `environment_manager.py` +~8/-4)
plus ~16 new tests and 2 existing test updates in `test_create_test_db.py` (~+320). The
footprint sits near the 400-line mark but is well under the 600-line review budget, so a
single PR is appropriate.

```text
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium
```

---

## 1. Infrastructure / Preparation

- [x] 1.1 Establish a green baseline: run `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"` and record the current pass/fail count before touching any source. Confirm `odoo_env/test_create_test_db.py` is discovered by this pattern.
- [x] 1.2 Confirm the test home: verify `TestQaCli` lives in `odoo_env/test_create_test_db.py` (NOT `test_qa.py`) and read the existing `TestQaCli` tests plus `OdooEnvTestCase` in `odoo_env/test_helpers.py` to reuse its `mock_get_manifest` / `OeConfig.reset` fixtures and `MockArgs` shape.

---

## 2. Implementation (Strict TDD — RED → GREEN)

> Note: steps 2.2–2.3 are interdependent (changing the `EnvironmentManager.qa()` signature
> temporarily breaks the `OdooEnv.qa()` caller). The full suite is expected to be red between
> 2.2.2 and 2.4; it returns to green in step 4.

### 2.1 `_installed_modules()` on `OdooEnv`

- [x] 2.1.1 **RED** — In `odoo_env/test_create_test_db.py`, under `TestQaCli`, add:
  - `test_installed_modules_uses_correct_psql_command` — assert the exact argv list `["docker", "exec", f"pg-{client}", "psql", "-U", "odoo", "-d", database, "-tAc", "SELECT name FROM ir_module_module WHERE state = 'installed'"]` and that the SQL string contains no module name (REQ-QAV-004).
  - `test_installed_modules_parses_psql_output` — mock `subprocess.run` to return `stdout="sale\nstock\n\n"`, returncode 0; assert `== {"sale", "stock"}`.
  - `test_installed_modules_returns_empty_on_error` — mock `returncode != 0`; assert `== set()`.
  - Run the three tests → they MUST fail (method absent).
- [x] 2.1.2 **GREEN** — Add `_installed_modules(self, database: str) -> set[str]` to `odoo_env/odooenv.py`, mirroring `_db_exists` (subprocess argv list, no shell, `capture_output=True, text=True, check=False`; empty set on non-zero returncode). Run the three tests → green.

### 2.2 `EnvironmentManager.qa()` — new signature + conditional verbs

- [x] 2.2.1 **RED** — In `TestQaCli`, add command-composition tests that call `EnvironmentManager.qa(database, install_modules, update_modules)` directly (mock `docker_client.get_run_command` to capture the `RunSpec`):
  - `test_qa_command_contains_test_enable` — `test_enable=True` present.
  - `test_qa_command_contains_log_level_test` — `log_level="test"` present.
  - `test_qa_command_omits_empty_verbs` — `install_modules=[]` omits `-i`; `update_modules=[]` omits `-u`; never an empty `-i ""`/`-u ""`.
  - `test_qa_single_command_for_mixed_modules` — returns exactly one `Command`.
  - Run → MUST fail (current signature is `qa(database, modules_to_test)`).
- [x] 2.2.2 **GREEN** — In `odoo_env/managers/environment_manager.py`, change `qa()` to `qa(self, database: str, install_modules: list[str], update_modules: list[str])`. Build `extra_args = ["-d", database]`, then conditionally `extend(["-i", ",".join(install_modules)])` / `extend(["-u", ",".join(update_modules)])` only when non-empty. Preserve ALL existing `RunSpec` settings (interactive/tty, `remove`, `network="odoo-net"`, volumes, links, env WDB + `ODOO_CONF=/dev/null`, `stop_after_init=True`, `log_level="test"`, `test_enable=True`). Update `step_msg` to reflect `install_modules + update_modules`. Run the four tests → green.

### 2.3 `OdooEnv.qa()` — guards, state query, partition, delegation

- [x] 2.3.1 **RED** — In `TestQaCli`, add `OdooEnv.qa()`-level tests (drive through `oe.build_commands()` with `MockArgs(modules_to_test=...)`, mocking `EnvironmentManager.discover_modules_in`, `OdooEnv._db_exists`, and `OdooEnv._installed_modules` as needed):
  - `test_qa_aborts_on_unknown_module` — `typo_modlue` not in on-disk set → `OeError`.
  - `test_qa_aborts_lists_all_unknown_modules` — two typos → message lists both, sorted.
  - `test_qa_all_skips_ondisk_guard` — `modules_to_test="all"` with mocked `discover_test_modules` → `discover_modules_in` NOT called.
  - `test_qa_aborts_when_test_db_missing` — `_db_exists` → False → `OeError`; assert `_installed_modules` NOT called.
  - `test_qa_db_error_suggests_create_test_db` — error message references `--create-test-db`.
  - `test_qa_partitions_modules_by_install_state` — `_installed_modules` returns a subset → assert delegation receives correct `install_modules`/`update_modules` lists.
  - `test_qa_all_new_modules_use_install_verb` — none installed → only `-i`.
  - `test_qa_all_installed_modules_use_update_verb` — all installed → only `-u`.
  - `test_qa_mixed_modules_produce_dual_verb_command` — mix → single command with both `-i` and `-u`.
  - Run → MUST fail (current `qa()` delegates with the old string signature and has no guards).
- [x] 2.3.2 **GREEN** — Rewrite `OdooEnv.qa(self, modules_to_test)` in `odoo_env/odooenv.py` in this exact order: (1) resolve `modules_list` ("all" via `TestRunner.discover_test_modules()` with empty-list abort, else split+strip comma-string); (2) on-disk guard via `EnvironmentManager.discover_modules_in(self.client.custom_modules_dir)`, skip for "all", `msg.err(f"Module(s) not found on disk: ...")` on unknown; (3) DB-exists guard reusing `self._db_exists(database)`, `msg.err` suggesting `--create-test-db`; (4) `installed = self._installed_modules(database)`; (5) partition `install_modules = sorted(requested - installed)`, `update_modules = sorted(requested & installed)`; (6) `return EnvironmentManager(self).qa(database, install_modules, update_modules)`. Run the nine tests → green.

---

## 3. Triangulation & Refactor

- [x] 3.1 Add a triangulation test asserting the SQL text is exactly the fixed string `SELECT name FROM ir_module_module WHERE state = 'installed'` with no `IN (...)` clause and no module name anywhere in the argv (locks REQ-QAV-004's no-interpolation guarantee beyond the argv-shape test).
- [x] 3.2 Add a determinism assertion: for a mixed set, `install_modules` and `update_modules` are both `sorted` (stable command output). Refactor `step_msg` in `EnvironmentManager.qa()` to join `install_modules + update_modules` cleanly, and re-run the full file to confirm no regression.

---

## 4. Testing & Verification

- [x] 4.1 Update the two existing `TestQaCli` tests broken by the signature change:
  - `test_qa_passes_full_module_name` — mock `_db_exists`→True, `discover_modules_in`→`["modulo_a_testear"]`, `_installed_modules`→`{"modulo_a_testear"}`; keep asserting `-u modulo_a_testear` (preserves the original "full name, not first char" intent).
  - `test_qa_all_expands_to_discovered_testable_modules` — mock `_db_exists`→True and `_installed_modules`→`{"mod_a","mod_b"}`; keep asserting the joined `-u` list.
  - Leave `test_qa_all_aborts_when_no_testable_modules` unchanged (still valid).
- [x] 4.2 Run the full suite: `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"` — expect all tests green, including pre-existing `TestCreateTestDb`, `TestClient`, and `TestQa` tests (no regressions outside this change).
- [x] 4.3 Cross-check every spec scenario in `specs/qa-verb/spec.md` (REQ-QAV-001 through REQ-QAV-006) against a passing test or explicit coverage, and record any gap as a follow-up (do not expand scope into Part B or the CI path).
