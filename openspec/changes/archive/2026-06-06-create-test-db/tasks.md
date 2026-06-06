# Tasks: create-test-db

**Change**: `create-test-db`
**Phase**: SDD tasks (breakdown for apply)
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-06

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~180–210 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | single-pr |

---

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr
400-line budget risk: Low

---

## Phase 1 — Infrastructure (test scaffolding)

### 1.1 Scaffold `TestCreateTestDb` test class

- [x] 1.1.1 Add `TestCreateTestDb(OdooEnvTestCase)` class to `odoo_env/test_oe.py`
- [x] 1.1.2 Import `EnvironmentManager` and `OeError` at top of test file (if not present; verify)
- [x] 1.1.3 Add `import sys` and `import builtins` at top of test file if not present
- [x] 1.1.4 Run `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest odoo_env.test_oe.TestCreateTestDb` — expect "no tests found" (class exists but empty, confirms import path works)
- **REQ coverage**: N/A (infrastructure)

---

## Phase 2 — RED: `discover_modules_in_cwd()` and `_build_module_command()` tests

### 2.1 Test `discover_modules_in_cwd()` — happy path and edges

- [x] 2.1.1 Write `test_discover_modules_finds_manifest_dirs`: patch `os.getcwd` to return `"/fake/cwd"`, patch `Path.iterdir` to yield entries `module_a/` (with `__manifest__.py`), `module_b/` (with `__manifest__.py`), `not_a_module/` (without), `some_file.txt` (file, not dir). Assert result is `["module_a", "module_b"]` (sorted).
- [x] 2.1.2 Write `test_discover_modules_empty_cwd`: patch `Path.iterdir` to return `[]`. Assert result is `[]`.
- [x] 2.1.3 Write `test_discover_modules_ignores_hidden_dirs`: patch `iterdir` to return `.git/` (dir but no `__manifest__.py`). Assert `.git` not in result.
- [x] 2.1.4 Write `test_discover_modules_ignores_root_manifest`: patch `iterdir` to return `__manifest__.py` as a file (not a dir). Assert not included.
- [x] 2.1.5 Write `test_discover_modules_does_not_recurse`: patch `iterdir` to return only `module_c/` (has `__manifest__.py`). Assert `["module_c"]` — extras in nested sub-subdirectories must not appear.
- [x] 2.1.6 Run tests — expect **FAIL** (RED): `AttributeError: type object 'EnvironmentManager' has no attribute 'discover_modules_in_cwd'`
- **REQ coverage**: REQ-CTDB-002 (all scenarios)
- **Design reference**: ADR 2, Testing seam 1

### 2.2 Test `_build_module_command(database, modules, "-i")` — install variant

- [x] 2.2.1 Write `test_build_module_command_install`: create `OdooEnv(MockArgs(debug=False, client="test_client"))`, instantiate `EnvironmentManager(oe)`, call `env_mgr._build_module_command("dimec_test", ["module_a", "module_b"], "-i")`. Assert single Command returned with command list containing: `"-i"`, `"module_a, module_b"` comma-separated, `"-d", "dimec_test"`, `"--stop-after-init"`, `"--logfile=false"`, and NOT containing `"--test-enable"`.
- [x] 2.2.2 Assert `usr_msg` starts with `"Installing "` and mentions database name.
- [x] 2.2.3 Run tests — expect **FAIL** (RED): `AttributeError: 'EnvironmentManager' object has no attribute '_build_module_command'`
- **REQ coverage**: REQ-CTDB-004
- **Design reference**: ADR 3, Testing seam 4

### 2.3 Test `update()` still works after extraction

- [x] 2.3.1 Write `test_update_still_works_after_refactor`: call `oe.update("test_client_prod", ["all"])`, assert single Command containing `"-u"`, `"all"`, `"-d", "test_client_prod"`, `"--stop-after-init"`.
- [x] 2.3.2 Assert `usr_msg` starts with `"Performing update of "`.
- [x] 2.3.3 Run tests — expect **PASS** (existing behavior, pre-refactor; confirms baseline)
- **REQ coverage**: regression guard for `oe --update`
- **Design reference**: ADR 3

---

## Phase 3 — GREEN: implement `discover_modules_in_cwd()` and `_build_module_command()`

### 3.1 Add `discover_modules_in_cwd()` static method

- [x] 3.1.1 Open `odoo_env/managers/environment_manager.py`. Add `import os` and `from pathlib import Path` at top
- [x] 3.1.2 Add `@staticmethod discover_modules_in_cwd()` per ADR 2 contract
- [x] 3.1.3 Run tests from 2.1 — expect **PASS** (GREEN).
- **REQ coverage**: REQ-CTDB-002
- **Design reference**: ADR 2

### 3.2 Extract `_build_module_command()` and refactor `update()`

- [x] 3.2.1 Add `_build_module_command(self, database, modules, verb)` method to `EnvironmentManager` per ADR 3 contract.
- [x] 3.2.2 Refactor `update()` to call `_build_module_command` with `-u` and preserve `"Performing update of"` prefix.
- [x] 3.2.3 Run tests from 2.2 and 2.3 — expect **PASS** (GREEN).
- **REQ coverage**: REQ-CTDB-004 (install variant), regression guard for `update()`
- **Design reference**: ADR 3

---

## Phase 4 — RED: `create_test_db()` guard and composition tests

### 4.1 Test zero-modules guard (REQ-CTDB-005)

- [x] 4.1.1 Write `test_create_test_db_zero_modules_aborts`: patch `EnvironmentManager.discover_modules_in_cwd` to return `[]`, create `OdooEnv(MockArgs(create_test_db=True, ...))`, call `oe.create_test_db()`. Assert `OeError` is raised with message containing `"no module"` or `"No module"` (case-insensitive match on message).
- [x] 4.1.2 Assert `_db_exists` is never called (optionally patch it first and assert `not called`).
- [x] 4.1.3 Run — expect **FAIL** (RED): `OdooEnv` has no `create_test_db()` method.
- **REQ coverage**: REQ-CTDB-005
- **Design reference**: ADR 6, Testing seam 2

### 4.2 Test DB-exists guard — confirm yes proceeds (REQ-CTDB-006)

- [x] 4.2.1 Write `test_create_test_db_confirm_yes_proceeds`: patch `EnvironmentManager.discover_modules_in_cwd` → `["module_a"]`, patch `OdooEnv._db_exists` → `True`, patch `sys.stdin.isatty` → `True`, patch `builtins.input` → `"y"`. Call `oe.create_test_db()`. Assert no exception raised, assert >0 Command objects returned.
- [x] 4.2.2 Run — expect **FAIL** (RED, no method).
- **REQ coverage**: REQ-CTDB-006 scenario 1
- **Design reference**: ADR 5, Testing seam 3

### 4.3 Test DB-exists guard — confirm no aborts (REQ-CTDB-006)

- [x] 4.3.1 Write `test_create_test_db_confirm_no_aborts`: same patches as 4.2.1 but `builtins.input` → `"n"`. Assert `OeError` raised with message containing `"Aborted"`.
- [x] 4.3.2 Run — expect **FAIL** (RED).
- **REQ coverage**: REQ-CTDB-006 scenario 2
- **Design reference**: ADR 5, Testing seam 3

### 4.4 Test DB-exists guard — non-interactive aborts (REQ-CTDB-006)

- [x] 4.4.1 Write `test_create_test_db_non_interactive_aborts`: patch `discover_modules_in_cwd` → `["module_a"]`, patch `_db_exists` → `True`, patch `sys.stdin.isatty` → `False`. Assert `OeError` raised with message containing `"not a terminal"` or `"non-interactive"`.
- [x] 4.4.2 Run — expect **FAIL** (RED).
- **REQ coverage**: REQ-CTDB-006 scenario 3
- **Design reference**: ADR 5, Testing seam 3

### 4.5 Test DB-exists guard — EOFError aborts (REQ-CTDB-006)

- [x] 4.5.1 Write `test_create_test_db_eof_aborts`: patch `discover_modules_in_cwd` → `["module_a"]`, patch `_db_exists` → `True`, patch `sys.stdin.isatty` → `True`, patch `builtins.input` to raise `EOFError`. Assert `OeError` raised with message containing `"input stream ended"`.
- [x] 4.5.2 Run — expect **FAIL** (RED).
- **REQ coverage**: REQ-CTDB-006 (EOFError edge case)
- **Design reference**: ADR 5

### 4.6 Test full command composition (REQ-CTDB-001, 003, 004, 007)

- [x] 4.6.1 Write `test_create_test_db_command_composition`: patch `discover_modules_in_cwd` → `["module_a", "module_b"]`, patch `_db_exists` → `False` (skip confirmation), patch `client.backup_dir` property to return a known test path, call `oe.create_test_db()`. Assert exactly 4 Command objects returned.
- [x] 4.6.2 Assert Command 0 (copy): `command[0]` is `["cp", f"{backup_dir}/bkp_test/test.zip", f"{backup_dir}/test.zip"]`, `usr_msg` contains `"Copying seed"`.
- [x] 4.6.3 Assert Command 1 (restore): `command` contains `DBTOOLS_IMAGE` and `"ZIPFILE=test.zip"` and `"NEW_DBNAME={client}_test"` and no `"DEACTIVATE"` env var (because `no_deactivate=True`).
- [x] 4.6.4 Assert Command 2 (rm): `command` is `["rm", f"{backup_dir}/test.zip"]`, `usr_msg` contains `"Removing temporary"`.
- [x] 4.6.5 Assert Command 3 (install): `command` contains `"-i"`, `"module_a, module_b"`, `"-d", "{client}_test"`, `"--stop-after-init"`, and does NOT contain `"--test-enable"`.
- [x] 4.6.6 Run — expect **FAIL** (RED, no method).
- **REQ coverage**: REQ-CTDB-001, 003, 004, 007
- **Design reference**: ADR 1, 4, 6, Testing seam 4, 5

### 4.7 Test seed-missing aborts

- [x] 4.7.1 Write `test_create_test_db_seed_missing_aborts`: patch `discover_modules_in_cwd` → `["module_a"]`, patch `_db_exists` → `False`, patch `Path.is_file` on seed path to return `False`. Assert `OeError` raised with message containing `"Seed database not found"` or `"seed"`.
- [x] 4.7.2 Run — expect **FAIL** (RED).
- **REQ coverage**: ADR 4 source-existence guard
- **Design reference**: ADR 4

### 4.8 Test dispatch from `build_commands()`

- [x] 4.8.1 Write `test_create_test_db_dispatched_from_build_commands`: create `OdooEnv(MockArgs(create_test_db=True, client="test_client"))`, patch `create_test_db` on the instance to return `["fake_cmd"]`. Call `oe.build_commands()`. Assert the patched `create_test_db` was called once and its return value is included in the result list.
- [x] 4.8.2 Alternatively, assert that `msg.err("create-test-db is not yet implemented")` is no longer raised (verify old dispatch is gone).
- [x] 4.8.3 Run — expect **FAIL** (RED, old `msg.err` still fires).
- **REQ coverage**: REQ-CTDB-001 (trigger)
- **Design reference**: ADR 1 dispatch change

---

## Phase 5 — GREEN: implement `create_test_db()`, `_db_exists()`, `_confirm_overwrite()`

### 5.1 Add `_db_exists()` and `_confirm_overwrite()` methods

 - [x] 5.1.1 Open `odoo_env/odooenv.py`. Add `import subprocess` and `import sys` at top if not already present.
 - [x] 5.1.2 Add `_db_exists(self, database)` method per ADR 5: `subprocess.run(["docker", "exec", f"pg-{self.client.name}", "psql", "-U", "odoo", "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{database}'"], capture_output=True, text=True)`. Return `True` if `returncode == 0 and stdout.strip() == "1"`.
 - [x] 5.1.3 Add `_confirm_overwrite(self, database)` method per ADR 5: guard `sys.stdin.isatty()` → `msg.err(...)` if false. `try: answer = input(...) except EOFError: msg.err(...)`. Return `answer.strip().lower() in ("y", "yes")`.
 - [x] 5.1.4 Run tests (GREEN)** (RED: `create_test_db` not yet implemented, so these tests fail on `AttributeError` for `create_test_db`). Confirm the error is about `create_test_db`, not `_db_exists` / `_confirm_overwrite`.
- **REQ coverage**: REQ-CTDB-006
- **Design reference**: ADR 5

### 5.2 Add `create_test_db()` method

 - [x] 5.2.1 Add `create_test_db(self)` method to `OdooEnv` per ADR 1 composition pseudocode:
  1. `modules = EnvironmentManager.discover_modules_in_cwd()`
  2. `if not modules: msg.err("No Odoo modules found...")`
  3. `database = f"{self.client.name}_test"`
  4. Guard: `seed_path = Path(self.client.backup_dir) / "bkp_test" / "test.zip"`; `if not seed_path.is_file(): msg.err(...)`
  5. Guard: `if self._db_exists(database): if not self._confirm_overwrite(database): msg.err("Aborted...")`
  6. Build Command list:
     - `Command(self, command=["cp", str(Path(self.client.backup_dir) / "bkp_test" / "test.zip"), str(Path(self.client.backup_dir) / "test.zip")], usr_msg="Copying seed database")`
     - `BackupManager(self, self.client.name).restore(database=database, backup_file="test.zip", no_deactivate=True)` — unpack/extend into command list
     - `Command(self, command=["rm", str(Path(self.client.backup_dir) / "test.zip")], usr_msg="Removing temporary seed copy")`
     - `env_mgr = EnvironmentManager(self); env_mgr._build_module_command(database, modules, "-i")` — unpack/extend
  7. Return the flat list.
 - [x] 5.2.2 Note: `BackupManager.restore()` and `_build_module_command()` each return `list[Command]`, not a single Command — use `commands += ...` or `commands.extend(...)` pattern.
 - [x] 5.2.3 Run tests (GREEN), 4.6, 4.7 — expect **PASS** (GREEN).
- **REQ coverage**: REQ-CTDB-001, 002, 003, 004, 005, 006, 007
- **Design reference**: ADR 1, 4, 5, 6

### 5.3 Wire dispatch in `build_commands()`

 - [x] 5.3.1 Wire dispatch in `build_commands()`.py`, replace lines ~90-91 (`if self._args.create_test_db: msg.err(...)`) with `if self._args.create_test_db: commands += self.create_test_db()`.
 - [x] 5.3.2 Run tests (GREEN) — expect **PASS** (GREEN).
 - [x] 5.3.3 Run full test suite suite: `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'` — expect all tests pass (no regressions).
- **REQ coverage**: REQ-CTDB-001 (dispatch)
- **Design reference**: ADR 1 dispatch change

---

## Phase 6 — REFACTOR: dead code and help text

### 6.1 Delete `odoo_env/create_database.py`

 - [x] 6.1.1 Delete file `odoo_env/create_database.py`.
 - [x] 6.1.2 Run full test suite — expect all pass (zero callers, no import breaks).
 - [x] 6.1.3 Verify no references remain: `grep -r "create_database" odoo_env/` should return no matches in `.py` files (may match in `.plantuml` docs — that's expected and acceptable).
- **REQ coverage**: proposal scope (dead-code removal)
- **Design reference**: ADR 7

### 6.2 Fix `--create-test-db` help text

 - [x] 6.2.1 In `odoo_env/oe.py`, change line ~179: `help="Create database with demo data."` → `help="Create a test database with all project modules"`.
 - [x] 6.2.2 Run full test suite — expect all pass.
- **REQ coverage**: proposal scope
- **Design reference**: ADR 1

---

## Phase 7 — VERIFY: full test suite and spec traceability

### 7.1 Run full test suite

 - [x] 7.1.1 Run: `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'`
 - [x] 7.1.2 Confirm all tests pass (zero failures, zero errors).
 - [x] 7.1.3 Confirm no existing tests regressed: all pre-existing test methods (e.g., `test_install`, `test_update`, `test_restore`, `test_qa`, etc.) still pass.

### 7.2 Trace implementation against spec scenarios

 - [x] 7.2.1 REQ-CTDB-001 (Trigger and naming): dispatch test (4.8) + composition test (4.6) confirm `create_test_db()` is called and database is `{client}_test`.
 - [x] 7.2.2 REQ-CTDB-002 (Module discovery): tests 2.1.1–2.1.5 cover all discovery scenarios.
 - [x] 7.2.3 REQ-CTDB-003 (Seed restore copy-up): composition test 4.6 asserts cp→restore→rm sequence.
 - [x] 7.2.4 REQ-CTDB-004 (Install with -i, no --test-enable): test 2.2 and 4.6.5.
 - [x] 7.2.5 REQ-CTDB-005 (Zero modules abort): test 4.1.
 - [x] 7.2.6 REQ-CTDB-006 (Existing DB confirmation): tests 4.2–4.5 cover confirm-yes, confirm-no, non-interactive, EOFError.
 - [x] 7.2.7 REQ-CTDB-007 (Order of operations): composition test 4.6 asserts exactly 4 commands in order; guard tests confirm abort-before-build.

---

## Risk notes

- **`_db_exists()` needs running pg container**: The method uses `docker exec pg-{client}` — unit tests mock it entirely. Integration testing not in scope. If the pg container is not running at production time, `create_test_db()` will detect during execution (restore/install steps fail).
- **`rstrip('/')` on backup_dir**: `client.backup_dir` returns a path ending with `/` (e.g., `/odoo_ar/…/backup_dir/`). The cp/rm commands must handle this:
  - `Path(backup_dir) / "test.zip"` works correctly even with trailing slash.
  - In the cp/rm string commands, use `str(Path(...))` to normalize.
- **postgres user is `odoo`**: Confirmed from `docker run -e POSTGRES_USER=odoo` in `run_environment()`. The `_db_exists` query uses `-U odoo`.
- **`BackupManager.restore()` returns `list[Command]`**: Not a single Command. Must use `extend`/`+=`.
- **`_build_module_command` returns `list[Command]`**: Same — must unpack.
- **`ConnectionResetError` from mocked tests**: When patching `subprocess.run` for `_db_exists`, ensure other tests restore the real `subprocess.run` — the `OdooEnvTestCase` tearDown handles this, but if adding class-level patches be careful.
