# Proposal: QA verb selection by real module install state

Change ID: `qa-verb-by-module-state`
Resolves: GitHub issue #128
Project: odoo-env (v0.16.10)
Language: English

## Intent

Make `oe -Q <module>` run tests for BOTH not-yet-installed and already-installed
modules by selecting the Odoo verb (`-i` vs `-u`) per module according to its real
install state in the `<client>_test` database, instead of the current hardcoded `-u`.

The goal is to eliminate the FALSE GREEN reported in issue #128: a brand-new module
with a `tests/` directory that is not yet installed is silently skipped by Odoo's
`-u` verb, so Odoo exits 0 reporting `0 failed, 0 error(s) of 0 tests`. This breaks
TDD for new modules — the exact workflow `oe -Q` exists to support.

## Problem (current state)

`EnvironmentManager.qa(database, modules_to_test)` in
`odoo_env/managers/environment_manager.py` (≈ lines 422-455) builds a single Odoo
command with a hardcoded update verb:

```python
extra_args=["-d", database, "-u", modules_to_test]
```

Odoo's test semantics under `--test-enable` are verb-sensitive and depend on the
module's install state:

- module NOT installed → `-i` installs it and runs its tests; `-u` does nothing (0 tests)
- module ALREADY installed → `-u` re-runs its tests; `-i` is skipped by Odoo (no rerun)

Odoo has no clean "reinstall". Therefore neither a fixed `-u` nor a fixed `-i` is
correct in the general case. A new module → `0 tests` false green; a stale/existing
module would break under a fixed `-i`. The verb MUST match each module's real state.

### Call chain (verified against code)

```
oe -Q <modules>
  → odoo_env/odooenv.py::qa(modules_to_test)
      resolves database = f"{client.name}_test"
      expands "all" via TestRunner.discover_test_modules()
  → odoo_env/managers/environment_manager.py::qa(database, modules_to_test)
      builds the single docker-run Odoo command  ← root cause (hardcoded -u)
```

## Proposed change (scope — Part A, the whole of THIS change)

1. Query the real install state of the requested modules from the `<client>_test`
   database before building the QA command.
   - Reuse the safe pattern from `odoo_env/odooenv.py::_db_exists`: run
     `docker exec pg-<client> psql -U odoo -d <db> -tAc` with a plain query.
   - Preferred query: `SELECT name FROM ir_module_module WHERE state = 'installed'`.
   - Partition the requested module set in Python against that result set.
     NO `IN (...)` interpolation and no user values pasted into SQL — zero SQL
     injection surface, consistent with the existing `_db_exists` design.
   - Classification: `state = 'installed'` → update partition (`-u`);
     row missing or `state = 'uninstalled'` → install partition (`-i`).

2. Build a SINGLE Odoo command carrying both verbs when both partitions are
   non-empty:

   ```
   odoo -d <db> -i <new,modules> -u <existing,modules> --test-enable --stop-after-init
   ```

   Odoo accepts both verbs in one invocation and resolves dependencies of the `-i`
   set. A verb is included ONLY when its partition is non-empty (never emit an empty
   `-i` or `-u`).

3. New guards (fail loud, never a false green):
   - If `<client>_test` does NOT exist → clear ERROR suggesting `--create-test-db`
     and abort. Do not run a broken psql query against a missing database.
   - If a requested module does NOT exist on disk (typo / wrong name) → clear
     "module not found" ERROR and abort.

## Affected modules

- `odoo_env/managers/environment_manager.py` — `qa()`: replace the hardcoded `-u`
  with per-partition verb construction; emit `-i`/`-u` only when non-empty. May
  reuse the existing `extra_args` scaffolding pattern from `_build_module_command`.
- `odoo_env/odooenv.py` — `qa()` wrapper: add the not-installed/installed state
  query helper (new private method following the `_db_exists` pattern), the
  test-DB-existence guard, and the module-exists-on-disk guard; pass the partitioned
  module sets down to `EnvironmentManager.qa`.
- `odoo_env/test_qa.py` — new/updated unit tests covering verb partitioning, both
  guards, and the single-command-with-both-verbs case (strict TDD; unittest).

## Non-goals (explicit — documented as follow-ups)

- **Part B (deferred to a separate change):** Turn "0 tests collected on a module
  that HAS a `tests/` directory" into an explicit ERROR. This requires changing the
  QA command execution model to streaming + output parsing (like
  `odoo_env/qa/runner.py::TestRunner._run_one`) plus a new `of (\d+) tests` parse.
  Out of scope here; document as a named follow-up.
- **CI verb unification (documented risk, not touched):**
  `odoo_env/qa/runner.py` (`_plain_module_cmd` / `_coverage_module_cmd`) uses a
  FIXED `-i` verb. It works only because the CI path restores a fresh test DB from a
  seed on each run, so every module is effectively not-installed. This inconsistency
  is recorded as a risk/note; unifying it is NOT part of this change.

## Risks

- **State-query correctness / timing.** The install state is read at QA-launch time
  via `docker exec`. If the postgres container or `<client>_test` DB is in an odd
  intermediate state, the partition could misclassify. Mitigated by the explicit
  test-DB-existence guard and by reusing the proven `_db_exists` invocation shape.
- **Odoo dual-verb behavior.** Relies on Odoo accepting `-i A -u B` in one command
  and resolving `-i` dependencies. This is standard Odoo behavior but couples us to
  it; a regression in a future Odoo version would surface here. Contained to the
  single QA command builder.
- **Divergence with the CI path.** The CI runner keeps its fixed `-i`. Two verb
  strategies now coexist (interactive `-Q` = per-state; CI = fixed `-i` on fresh
  seed). Documented deliberately; a future change may unify them.
- **`ir_module_module` name matching.** Odoo technical module names must match the
  requested names exactly. The on-disk module-exists guard reduces typo risk, but a
  module present on disk yet under a different technical name would classify as
  not-installed (`-i`) — acceptable and correct for that case.

## Rollback plan

The change is isolated to (a) verb selection inside `EnvironmentManager.qa` and
(b) the new state-query helper + guards in `odoo_env/odooenv.py::qa`. No data
migrations, no schema changes, no changes to the CI path. Reverting the commit
restores the previous hardcoded `-u` behavior with no residual state. The added
unit tests are self-contained and revert with the same commit.

## Success criteria

1. `oe -Q <new_module>` (module present on disk, not installed in `<client>_test`)
   installs the module with `-i` and actually RUNS its tests — no `0 tests` false
   green.
2. `oe -Q <existing_module>` (already installed) re-runs its tests with `-u`.
3. `oe -Q <new>,<existing>` produces a SINGLE Odoo command
   `odoo -d <db> -i <new> -u <existing> --test-enable --stop-after-init`; empty
   partitions omit their verb.
4. `oe -Q ...` against a missing `<client>_test` DB aborts with a clear error
   suggesting `--create-test-db` (no broken psql query, no false green).
5. `oe -Q <typo_module>` (not on disk) aborts with a clear "module not found" error.
6. Module-state query uses the safe `_db_exists`-style psql invocation with no SQL
   interpolation of module names (Python-side partitioning only).
7. All unit tests pass:
   `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`.

## Delivery constraints

- Strict TDD (unittest). Test command:
  `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`.
- Delivery strategy: single PR, review budget 600 lines.
