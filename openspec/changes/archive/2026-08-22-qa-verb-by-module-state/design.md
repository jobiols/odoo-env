# Design: QA Verb Selection by Module State

Change ID: `qa-verb-by-module-state`
Spec: `specs/qa-verb/spec.md`
Resolves: GitHub issue #128

## Overview

This design addresses Part A of issue #128: making `oe -Q <module>` select the correct Odoo verb (`-i` vs `-u`) per module based on its real install state in the `<client>_test` database.

The core insight is that Odoo's test semantics under `--test-enable` are verb-sensitive:

- Module NOT installed → `-i` installs it and runs its tests; `-u` does nothing (0 tests)
- Module ALREADY installed → `-u` re-runs its tests; `-i` is skipped

Therefore, a single hardcoded verb is incorrect. The verb MUST match each module's real state.

---

## Architecture Decision Records

### ADR-1: Module State Query Location and Shape

**Decision:** Add a new private method `_installed_modules(database: str) -> set[str]` on the `OdooEnv` class in `odoo_env/odooenv.py`.

**Context:** We need to query which modules are installed in the test database. There are three placement options:

1. On `OdooEnv` (chosen)
2. On `EnvironmentManager`
3. Inline in the `qa()` method

**Rationale:**

- `OdooEnv` already owns `_db_exists()`, which uses the exact same subprocess pattern (`docker exec pg-<client> psql ...`). Placing `_installed_modules()` alongside maintains cohesion.
- The query is database-scoped, and `OdooEnv.qa()` already resolves `database = f"{self._client.name}_test"` before delegating to `EnvironmentManager`. The state query naturally fits at this same layer.
- `EnvironmentManager.qa()` focuses on building the Odoo run command. Adding postgres querying there violates its single responsibility.

**Shape:**

```python
def _installed_modules(self, database: str) -> set[str]:
    """Return names of all installed modules in the given database.

    Queries ir_module_module via docker exec on pg-{client}.
    Returns an empty set on any error (container down, DB missing, etc.).

    Uses the same safe subprocess pattern as _db_exists:
    - subprocess argv list (no shell)
    - capture_output=True, text=True, check=False
    - Fixed SQL text (no interpolation of module names)
    """
    result = subprocess.run(
        [
            "docker",
            "exec",
            f"pg-{self.client.name}",
            "psql",
            "-U",
            "odoo",
            "-d",
            database,
            "-tAc",
            "SELECT name FROM ir_module_module WHERE state = 'installed'",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
```

**Alternatives Rejected:**

1. **`IN (...)` clause with module names:** Rejected per REQ-QAV-004. Interpolating user-provided module names into SQL (e.g., `WHERE name IN ('mod_a','mod_b')`) creates a SQL-injection surface. The spec explicitly requires Python-side partitioning against a full result set.

2. **Query inside `EnvironmentManager.qa()`:** Rejected because `EnvironmentManager` is about Docker command composition, not postgres querying. This would violate separation of concerns.

---

### ADR-2: Partition Threading from OdooEnv to EnvironmentManager

**Decision:** Change the `EnvironmentManager.qa()` signature to accept two lists instead of a comma-string:

```python
# Current signature
def qa(self, database: str, modules_to_test: str) -> list[Command]:

# New signature
def qa(
    self,
    database: str,
    install_modules: list[str],
    update_modules: list[str]
) -> list[Command]:
```

**Context:** The current signature passes `modules_to_test` as a pre-joined comma-string. The new flow requires passing two partitions (install vs update) so `EnvironmentManager.qa()` can emit both verbs conditionally.

**Rationale:**

- Passing structured data (two lists) is cleaner than passing a comma-string that would need re-parsing.
- `EnvironmentManager.qa()` already builds `extra_args` internally; it can emit `-i`/`-u` with their respective module lists based on non-emptiness.
- Keeps partitioning logic in `OdooEnv.qa()` (the orchestrator), while `EnvironmentManager.qa()` focuses on command composition.

**Partitioning Logic (in `OdooEnv.qa()`):**

```python
installed = self._installed_modules(database)
requested = set(modules_list)  # from comma-string split

update_modules = sorted(requested & installed)      # intersection
install_modules = sorted(requested - installed)     # difference
```

**Why NOT reuse `_build_module_command()`:**

`_build_module_command()` is designed for single-verb operations (install OR update) and does NOT add `--test-enable` or `log_level=test`. The QA path requires:

- `--test-enable` (tests run)
- `--log-level=test` (Odoo logging for tests)
- Conditional dual verbs (`-i` AND `-u` when both partitions non-empty)
- WDB environment variables

These QA-specific requirements make `qa()` distinct from `_build_module_command()`. Attempting to unify them would overcomplicate `_build_module_command()` with test-specific flags. Keep them separate.

---

### ADR-3: Module-Exists-on-Disk Guard Location and Logic

**Decision:** Add the on-disk validation guard in `OdooEnv.qa()`, before the database existence check, using `EnvironmentManager.discover_modules_in()` as the authoritative source.

**Context:** REQ-QAV-006 requires aborting with a clear "module not found" error when a requested module doesn't exist on disk (typo protection).

**Discovery Sources Analyzed:**

1. **`TestRunner.discover_test_modules()`** — Scans CWD for subdirs with `__manifest__.py` AND `tests/`. Used by `-Q all`. However, it's too restrictive: a requested module may legitimately exist on disk without a `tests/` directory (Part B will handle the "0 tests" case).

2. **`EnvironmentManager.discover_modules_in(base_dir)`** — Scans a given directory for subdirs with `__manifest__.py` only. Already used by `create_test_db()`. More appropriate: validates that the module is a valid Odoo module on disk, regardless of whether it has tests.

**Decision Details:**

- **Authoritative source:** `EnvironmentManager.discover_modules_in(self.client.custom_modules_dir)`
- **Guard checks:** `__manifest__.py` presence only, NOT `tests/` presence
- **Rationale:** A module without `tests/` is still a valid module to request. Whether it has tests to run is a separate concern (Part B). The on-disk guard prevents typos, not missing-tests detection.

**Special Case — `-Q all`:**

When `modules_to_test == "all"`, the module list comes from `TestRunner.discover_test_modules()`. By construction, these modules exist on disk (discovery wouldn't return them otherwise). The on-disk guard can skip validation in this case.

**Guard Location in Flow:**

```
OdooEnv.qa(modules_to_test)
  │
  ├─ IF modules_to_test == "all":
  │     modules_list = TestRunner.discover_test_modules()  # already validated
  │     [skip on-disk guard — modules came from discovery]
  │ ELSE:
  │     modules_list = split comma-string
  │     on_disk = set(EnvironmentManager.discover_modules_in(custom_modules_dir))
  │     unknown = set(modules_list) - on_disk
  │     IF unknown:
  │         msg.err(f"Module(s) not found on disk: {', '.join(sorted(unknown))}")
  │
  └─ [continue to DB guard, state query, partition, delegate]
```

---

### ADR-4: Order of Operations in the New QA Flow

**Decision:** Implement guards and operations in this order:

```
1. Module resolution (expand "all" or split comma-string)
2. ON-DISK GUARD: Validate all requested modules exist on disk (skip for "all")
3. DB-EXISTS GUARD: Check <client>_test exists, abort suggesting --create-test-db
4. STATE QUERY: Query ir_module_module for installed modules
5. PARTITION: Classify into install_modules and update_modules
6. DELEGATE: Call EnvironmentManager.qa(database, install_modules, update_modules)
```

**Rationale:**

- **On-disk guard first (step 2):** Catches typos early, before any docker/psql execution. A typo is a user error; don't waste time querying postgres for a misspelled module.

- **DB-exists guard second (step 3):** If the test database doesn't exist, the state query would fail with a psql error. Guard first with a clear message suggesting `--create-test-db`. Reuses the existing `_db_exists()` method.

- **State query third (step 4):** Only runs after we know the DB exists. Uses `_installed_modules()`.

- **Partition fourth (step 5):** Pure Python set operations. No external calls.

- **Delegate last (step 6):** `EnvironmentManager.qa()` builds the command once we have validated inputs.

**Error Handling Pattern:**

All guards use the existing `msg.err(text)` convention, which prints in red and raises `OeError`. This is consistent with `create_test_db()` and other methods.

---

### ADR-5: Extra Args Construction in EnvironmentManager.qa()

**Decision:** Emit `-i` and `-u` conditionally based on partition non-emptiness.

**Current Implementation (hardcoded -u):**

```python
extra_args=["-d", database, "-u", modules_to_test]
```

**New Implementation:**

```python
extra_args = ["-d", database]
if install_modules:
    extra_args.extend(["-i", ",".join(install_modules)])
if update_modules:
    extra_args.extend(["-u", ",".join(update_modules)])
```

**Invariants Preserved:**

The following must remain unchanged from the current `qa()` implementation:

| Aspect | Current | New (unchanged) |
|--------|---------|-----------------|
| TTY/interactive | `sys.stdin.isatty()` | Same |
| Network | `network="odoo-net"` | Same |
| Volumes | `_get_normal_mountings()` + debug | Same |
| Links | `pg-{client}` → `db` | Same |
| Environment | WDB vars + `ODOO_CONF=/dev/null` | Same |
| `stop_after_init` | `True` | Same |
| `log_level` | `"test"` | Same |
| `test_enable` | `True` | Same |
| Remove container | `remove=True` | Same |

**Command Shape Examples:**

1. **All modules not installed:** `odoo -d dimec_test -i mod_a,mod_b --test-enable --stop-after-init ...`
2. **All modules installed:** `odoo -d dimec_test -u mod_a,mod_b --test-enable --stop-after-init ...`
3. **Mixed:** `odoo -d dimec_test -i new_mod -u existing_mod --test-enable --stop-after-init ...`
4. **Single new:** `odoo -d dimec_test -i new_mod --test-enable --stop-after-init ...`
5. **Single existing:** `odoo -d dimec_test -u existing_mod --test-enable --stop-after-init ...`

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CLI: oe -Q mod_a,mod_b                                                      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OdooEnv.qa(modules_to_test="mod_a,mod_b")                                   │
│                                                                             │
│   1. modules_list = ["mod_a", "mod_b"]                                      │
│                                                                             │
│   2. ON-DISK GUARD ─────────────────────────────────────────────────────┐   │
│      on_disk = EnvironmentManager.discover_modules_in(custom_modules_dir)   │
│      unknown = {"mod_a", "mod_b"} - on_disk                             │   │
│      if unknown: msg.err("Module(s) not found: ...")  ─────────────────►│ERR│
│                                                                             │
│   3. DB-EXISTS GUARD ───────────────────────────────────────────────────┐   │
│      if not _db_exists("dimec_test"):                                   │   │
│          msg.err("Test database ... use --create-test-db")  ───────────►│ERR│
│                                                                             │
│   4. STATE QUERY                                                            │
│      installed = _installed_modules("dimec_test")                           │
│      # e.g., {"mod_b", "sale", "stock"}                                     │
│                                                                             │
│   5. PARTITION                                                              │
│      update_modules  = ["mod_b"]    # {"mod_a","mod_b"} ∩ installed         │
│      install_modules = ["mod_a"]    # {"mod_a","mod_b"} - installed         │
│                                                                             │
│   6. DELEGATE                                                               │
│      return EnvironmentManager.qa(                                          │
│          database="dimec_test",                                             │
│          install_modules=["mod_a"],                                         │
│          update_modules=["mod_b"]                                           │
│      )                                                                      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ EnvironmentManager.qa(database, install_modules, update_modules)            │
│                                                                             │
│   extra_args = ["-d", "dimec_test"]                                         │
│   if install_modules:   # ["mod_a"]                                         │
│       extra_args += ["-i", "mod_a"]                                         │
│   if update_modules:    # ["mod_b"]                                         │
│       extra_args += ["-u", "mod_b"]                                         │
│                                                                             │
│   cmd_list = docker_client.get_run_command(RunSpec(                         │
│       ...,                                                                  │
│       test_enable=True,                                                     │
│       log_level="test",                                                     │
│       extra_args=["-d", "dimec_test", "-i", "mod_a", "-u", "mod_b"]         │
│   ))                                                                        │
│                                                                             │
│   return [Command(self.parent, command=cmd_list, usr_msg="...")]            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Final docker command:                                                       │
│ docker run ... odoo -d dimec_test -i mod_a -u mod_b --test-enable           │
│                      --stop-after-init --log-level=test                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Changes

### 1. `odoo_env/odooenv.py`

| Change Type | Description |
|-------------|-------------|
| **ADD** | `_installed_modules(self, database: str) -> set[str]` — Query installed modules via docker exec psql |
| **MODIFY** | `qa(self, modules_to_test)` — Add on-disk guard, DB-exists guard, state query, partitioning; change delegation signature |

**Method Changes:**

```python
# BEFORE (simplified)
def qa(self, modules_to_test):
    if modules_to_test == "all":
        modules = TestRunner.discover_test_modules()
        modules_to_test = ",".join(modules)
    database = f"{self._client.name}_test"
    return EnvironmentManager(self).qa(database, modules_to_test)

# AFTER (simplified)
def qa(self, modules_to_test):
    database = f"{self._client.name}_test"

    # Step 1: Module resolution
    if modules_to_test == "all":
        modules_list = TestRunner.discover_test_modules()
        if not modules_list:
            msg.err("No testable modules found ...")
    else:
        modules_list = [m.strip() for m in modules_to_test.split(",")]

        # Step 2: On-disk guard
        on_disk = set(EnvironmentManager.discover_modules_in(
            self.client.custom_modules_dir
        ))
        unknown = set(modules_list) - on_disk
        if unknown:
            msg.err(f"Module(s) not found on disk: {', '.join(sorted(unknown))}")

    # Step 3: DB-exists guard
    if not self._db_exists(database):
        msg.err(
            f"Test database '{database}' does not exist.\n"
            "  Create it first with: oe --create-test-db"
        )

    # Step 4: State query
    installed = self._installed_modules(database)

    # Step 5: Partition
    requested = set(modules_list)
    install_modules = sorted(requested - installed)
    update_modules = sorted(requested & installed)

    # Step 6: Delegate
    return EnvironmentManager(self).qa(database, install_modules, update_modules)
```

### 2. `odoo_env/managers/environment_manager.py`

| Change Type | Description |
|-------------|-------------|
| **MODIFY** | `qa(self, database, install_modules, update_modules)` — Accept two lists, emit verbs conditionally |

**Method Changes:**

```python
# BEFORE
def qa(self, database, modules_to_test):
    ...
    extra_args=["-d", database, "-u", modules_to_test],
    ...

# AFTER
def qa(self, database, install_modules, update_modules):
    ...
    extra_args = ["-d", database]
    if install_modules:
        extra_args.extend(["-i", ",".join(install_modules)])
    if update_modules:
        extra_args.extend(["-u", ",".join(update_modules)])
    ...

    # Update user message to reflect both partitions
    all_modules = install_modules + update_modules
    step_msg = (
        f"Performing tests on module(s) {', '.join(all_modules)} "
        f"for client {self.parent._client.name} and database {database}"
    )
```

### 3. `odoo_env/test_create_test_db.py`

| Change Type | Description |
|-------------|-------------|
| **ADD** | Test cases for `_installed_modules()` |
| **ADD** | Test cases for on-disk guard |
| **ADD** | Test cases for DB-exists guard |
| **ADD** | Test cases for partitioning logic |
| **ADD** | Test cases for dual-verb command composition |
| **MODIFY** | Existing `TestQaCli` tests may need signature updates |

**Important Discovery:** The existing `oe -Q` CLI tests live in `odoo_env/test_create_test_db.py` (class `TestQaCli`), NOT in `test_qa.py`. New tests should be added to this same class/file for consistency.

---

## Contract Boundaries

### OdooEnv.qa() Contract (Updated)

**Responsibilities:**

- Expand "all" via `TestRunner.discover_test_modules()`
- Validate modules exist on disk (on-disk guard)
- Validate test database exists (DB-exists guard)
- Query installed module state
- Partition into install/update lists
- Delegate to `EnvironmentManager.qa()`

**Preconditions:**

- `self._client` is set
- Postgres container `pg-{client}` is running (for guards and state query)

**Postconditions:**

- Returns `list[Command]` representing the QA docker run command
- Raises `OeError` on any guard failure

### EnvironmentManager.qa() Contract (Updated)

**Responsibilities:**

- Build docker run command with conditional `-i`/`-u` verbs
- Include all QA-specific flags (`--test-enable`, `log_level=test`, etc.)
- Compose volumes, links, env, TTY settings

**Preconditions:**

- `database` is a valid database name
- `install_modules` and `update_modules` are lists (may be empty, but not both empty)

**Postconditions:**

- Returns `list[Command]` with exactly one Command
- Command includes `-i` verb only if `install_modules` is non-empty
- Command includes `-u` verb only if `update_modules` is non-empty

### _installed_modules() Contract (New)

**Responsibilities:**

- Query `ir_module_module WHERE state = 'installed'` via docker exec psql
- Parse stdout into a set of module names

**Preconditions:**

- Postgres container `pg-{client}` is running
- Database exists (caller should guard)

**Postconditions:**

- Returns `set[str]` of installed module names
- Returns empty set on any error (non-zero return code, container down, etc.)

---

## Test Strategy

### Unit Test Coverage (Strict TDD)

Tests go in `odoo_env/test_create_test_db.py` under class `TestQaCli`.

**1. `_installed_modules()` tests:**

- `test_installed_modules_parses_psql_output` — Mock subprocess.run, verify set parsing
- `test_installed_modules_returns_empty_on_error` — Mock returncode != 0, verify empty set
- `test_installed_modules_uses_correct_psql_command` — Verify argv structure

**2. On-disk guard tests:**

- `test_qa_aborts_on_unknown_module` — Request non-existent module, verify OeError
- `test_qa_aborts_lists_all_unknown_modules` — Multiple typos, verify error message
- `test_qa_all_skips_ondisk_guard` — `-Q all` doesn't run on-disk check

**3. DB-exists guard tests:**

- `test_qa_aborts_when_test_db_missing` — Mock `_db_exists` → False, verify OeError
- `test_qa_db_error_suggests_create_test_db` — Verify error message contains hint

**4. Partitioning tests:**

- `test_qa_partitions_modules_by_install_state` — Mock `_installed_modules`, verify lists
- `test_qa_all_new_modules_use_install_verb` — All modules not installed → `-i` only
- `test_qa_all_installed_modules_use_update_verb` — All modules installed → `-u` only
- `test_qa_mixed_modules_produce_dual_verb_command` — Mix → both `-i` and `-u`

**5. Command composition tests:**

- `test_qa_command_contains_test_enable` — Verify `--test-enable` present
- `test_qa_command_contains_log_level_test` — Verify `--log-level=test` present
- `test_qa_command_omits_empty_verbs` — No `-i` or `-u` with empty string
- `test_qa_single_command_for_mixed_modules` — Verify exactly one Command returned

### Test Command

```bash
PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"
```

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Postgres container not running | Medium | High | DB-exists guard catches this with clear error |
| ir_module_module query returns unexpected format | Low | Medium | Empty-set fallback; manual testing with real Odoo |
| Module on disk but different technical name | Low | Low | On-disk guard uses manifest presence; state query uses Odoo's module name. Mismatch = treated as not-installed → `-i` (correct) |
| Odoo changes dual-verb semantics | Very Low | High | Document reliance on Odoo's `-i A -u B` support; version-specific testing |

---

## Non-Goals (Documented)

Per proposal scope, this design does NOT cover:

1. **Part B:** Turning "0 tests collected on a module with `tests/`" into an ERROR. That requires streaming output parsing.

2. **CI path (`odoo_env/qa/runner.py`):** The CI runner keeps its fixed `-i` verb. That's correct for its fresh-seed-restore model.

3. **`-Q all` discovery changes:** The existing expansion via `TestRunner.discover_test_modules()` is unchanged; only the verb selection applied to the resulting list is affected.
