# qa-verb Specification

## Purpose

Defines how the `oe -Q <modules>` selective test command selects the Odoo verb
(`-i` install vs `-u` update) **per module** according to that module's real
install state in the `<client>_test` database, instead of the previous hardcoded
`-u`. The goal is to eliminate the false green reported when a brand-new module
(not yet installed) is silently skipped by `-u` and Odoo exits 0 with
`0 failed, 0 error(s) of 0 tests`.

This spec covers only the interactive `oe -Q` path (Part A). It does not cover
the coverage/CI engine (`odoo_env/qa`) or its fixed `-i` verb (see
Non-Requirements).

## Requirements

### Requirement: REQ-QAV-001 — Not-installed module runs with the install verb (`-i`)

When `oe -Q <new>` is invoked for a module that is present on disk but NOT in the
installed set of the `<client>_test` database, the system MUST build an Odoo
command that installs the module with `-i <new>`, so that the module's tests
actually run. The system MUST NOT use `-u` for that module and MUST NOT produce a
false green (a run that reports `0 tests` because the module was never installed).

#### Scenario: New module is installed and its tests run

- GIVEN the active client is `dimec` and the test database is `dimec_test`
- AND module `my_new_module` exists on disk but is NOT returned by the
  `state='installed'` query against `dimec_test`
- WHEN `oe -Q my_new_module` is invoked
- THEN the system MUST build an Odoo command containing `-i my_new_module`
- AND the command MUST include `--test-enable` and `--stop-after-init`
- AND the command MUST NOT contain `-u my_new_module`

#### Scenario: A new module never falls back to a false-green update

- GIVEN module `my_new_module` exists on disk and is not installed
- WHEN the QA command is built
- THEN the built command MUST NOT use `-u` for `my_new_module`
- AND the module MUST be installed (via `-i`) so its tests run, rather than being
  skipped with `0 tests`

### Requirement: REQ-QAV-002 — Installed module re-runs its tests with the update verb (`-u`)

When `oe -Q <existing>` is invoked for a module that is already installed in the
`<client>_test` database, the system MUST build an Odoo command that re-runs its
tests with `-u <existing>`. The system MUST NOT use `-i` for that module, because
Odoo skips re-running tests for an already-installed module under `-i`.

#### Scenario: Installed module re-runs with the update verb

- GIVEN the active client is `dimec` and the test database is `dimec_test`
- AND module `sale` is present in the `state='installed'` result set of
  `dimec_test`
- WHEN `oe -Q sale` is invoked
- THEN the system MUST build an Odoo command containing `-u sale`
- AND the command MUST include `--test-enable` and `--stop-after-init`
- AND the command MUST NOT contain `-i sale`

### Requirement: REQ-QAV-003 — Mixed set produces a single command carrying both verbs

When `oe -Q` is invoked with a mixed set of modules (some not installed, some
already installed), the system MUST produce exactly ONE Odoo command that carries
both verbs:

```
odoo -d <db> -i <new,modules> -u <existing,modules> --test-enable --stop-after-init
```

A verb MUST be omitted entirely when its partition is empty. The system MUST
never emit an empty `-i` or an empty `-u`.

#### Scenario: Mixed new and existing modules produce a single dual-verb command

- GIVEN the test database is `dimec_test`
- AND `my_new_module` is not installed and `sale` is installed
- WHEN `oe -Q my_new_module,sale` is invoked
- THEN the system MUST build a single Odoo command of the form
  `odoo -d dimec_test -i my_new_module -u sale --test-enable --stop-after-init`
- AND the command MUST NOT be split into two separate Odoo invocations

#### Scenario: All-new modules omit the update verb

- GIVEN `mod_a` and `mod_b` are both not installed
- WHEN `oe -Q mod_a,mod_b` is invoked
- THEN the built command MUST contain `-i mod_a,mod_b`
- AND the built command MUST NOT contain an `-u` token

#### Scenario: All-installed modules omit the install verb

- GIVEN `sale` and `stock` are both installed
- WHEN `oe -Q sale,stock` is invoked
- THEN the built command MUST contain `-u sale,stock`
- AND the built command MUST NOT contain an `-i` token

### Requirement: REQ-QAV-004 — Module install state resolved via a safe psql query and Python partitioning

The system MUST determine each requested module's install state by querying the
`<client>_test` database once with a safe `docker exec` psql invocation that
follows the existing `_db_exists` shape (subprocess argv list, no shell,
captured output, `check=False`):

```
docker exec pg-<client> psql -U odoo -d <db> -tAc "SELECT name FROM ir_module_module WHERE state = 'installed'"
```

The query text MUST be a fixed string. Module names MUST NOT be interpolated into
the SQL (no `IN (...)` clause and no concatenation), preserving a zero
SQL-injection surface. The system MUST partition the requested module set in
Python against the query result set.

State classification rule:

- `state='installed'` (module name present in the query result) → update
  partition (`-u`).
- row missing OR `state='uninstalled'` (module name absent from the query
  result) → install partition (`-i`).

#### Scenario: Installed row is classified to the update partition

- GIVEN the state query returns module name `sale`
- AND the requested set is `["sale"]`
- WHEN Python partitioning runs
- THEN `sale` MUST be placed in the update (`-u`) partition

#### Scenario: Missing row is classified to the install partition

- GIVEN the state query returns no row for `my_new_module`
- AND the requested set is `["my_new_module"]`
- WHEN Python partitioning runs
- THEN `my_new_module` MUST be placed in the install (`-i`) partition

#### Scenario: A module in the uninstalled state is classified to the install partition

- GIVEN `my_module` exists in `ir_module_module` with `state='uninstalled'`
  (and is therefore absent from the `state='installed'` result set)
- WHEN Python partitioning runs
- THEN `my_module` MUST be placed in the install (`-i`) partition

#### Scenario: No SQL interpolation of module names

- GIVEN the requested set contains arbitrary module names
- WHEN the state query is constructed
- THEN the SQL text MUST be the fixed string
  `SELECT name FROM ir_module_module WHERE state = 'installed'`
- AND no module name MUST appear anywhere in the SQL text
- AND the module names MUST NOT be passed via any `IN (...)` clause

### Requirement: REQ-QAV-005 — Guard: missing test database aborts

When `oe -Q` runs against a client whose `<client>_test` database does not exist,
the system MUST abort with a clear error suggesting `--create-test-db`. The
system MUST NOT run a psql state query against the missing database, and MUST NOT
build or execute an Odoo test command (no false green).

#### Scenario: Missing test database aborts before any psql query

- GIVEN the active client is `dimec`
- AND the database `dimec_test` does not exist
- WHEN `oe -Q my_module` is invoked
- THEN the system MUST abort with an error that references `--create-test-db`
- AND the system MUST NOT run the `docker exec pg-dimec psql ...` state query
- AND no Odoo test command MUST be built or executed

### Requirement: REQ-QAV-006 — Guard: requested module not on disk aborts

When `oe -Q` is invoked with a requested module name that does not exist on disk
(e.g. a typo), the system MUST abort with a clear "module not found" error and
MUST NOT proceed to build or execute an Odoo command (no false green).

#### Scenario: Unknown module name aborts with a module-not-found error

- GIVEN the active client is `dimec`
- AND module `typo_modlue` does not exist on disk
- WHEN `oe -Q typo_modlue` is invoked
- THEN the system MUST abort with a clear error indicating the module was not found
- AND no Odoo test command MUST be built or executed

#### Scenario: A mixed set with one unknown module aborts

- GIVEN the requested set is `["sale", "typo_modlue"]`
- AND `typo_modlue` does not exist on disk
- WHEN `oe -Q sale,typo_modlue` is invoked
- THEN the system MUST abort with a clear "module not found" error
- AND no Odoo test command MUST be built or executed for any module

## Non-Requirements (explicitly out of scope)

The following behaviors are intentionally NOT specified and MUST NOT be
implemented in this change:

- **Part B — "0 tests" ERROR detection (deferred).** Turning "a module that has a
  `tests/` directory but collects 0 tests" into an explicit ERROR requires a
  streaming + output-parsing execution model and a new
  `of (\d+) tests` parse. This is a separate follow-up change and is NOT covered
  here.
- **CI-path verb unification.** `odoo_env/qa/runner.py`
  (`_plain_module_cmd` / `_coverage_module_cmd`) keeps its fixed `-i` verb,
  which is correct only because the CI path restores a fresh seed test database.
  Unifying the CI path with the per-state `oe -Q` strategy is NOT part of this
  change.
- **`oe -Q all` discovery semantics.** The existing `-Q all` expansion via
  `TestRunner.discover_test_modules()` (modules with a `tests/` directory) is
  unchanged; only the verb selection applied to the resulting module list is
  affected.
