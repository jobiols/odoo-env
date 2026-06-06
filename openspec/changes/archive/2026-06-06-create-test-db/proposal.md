# Proposal: `create-test-db`

**Change**: `create-test-db`
**Phase**: Proposal
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-06

## Problem

`oe` exposes a `--create-test-db` flag (`odoo_env/oe.py:179`) but it is
unimplemented: the dispatch in `odoo_env/odooenv.py:90-91` only raises
`msg.err("create-test-db is not yet implemented.")`. Teams currently rely on a
per-project bash script (`create_test_db.sh`) copied into each client repo to
build a throwaway test database. That script duplicates logic across projects,
hardcodes the client name, and lives outside the tool's tested codebase.

## What we want

Implement `--create-test-db` natively in `oe` so that a single command:

1. Restores a known **empty seed database** into `{client}_test`.
2. Installs **all of the current project's own modules** into that database.

The result is a clean, reproducible test database for the active client, with no
test execution (install only).

## Scope

In scope for this slice:

- Implement `OdooEnv.create_test_db()` and wire the dispatch in
  `build_commands()` (replace the `msg.err`).
- **Module discovery**: scan the **current working directory (CWD)** for its
  immediate subdirectories that contain an `__manifest__.py`. Install **all** of
  them. No `tests/`-folder filtering.
- **Seed restore (copy-up)**: copy `backup_dir/bkp_test/test.zip` into
  `backup_dir/`, restore into `{client}_test` (equivalent to
  `oe --restore -d {client}_test --no-deactivate -f test.zip`), then remove the
  temporary copy. The `BackupManager.restore` contract is **not** modified.
- **Install step**: reuse the existing docker-run builder used by
  `EnvironmentManager.update()` but emit `-i` (install) instead of `-u`
  (update), with `--stop-after-init -d {client}_test`. No `--test-enable`.
- Fix the misleading `--create-test-db` help text in `oe.py`.
- **Remove dead legacy code** `odoo_env/create_database.py`: an unwired,
  pre-Command-pattern implementation of the same idea. It is not referenced
  anywhere and is broken (`subprocess.call(command_string)` without
  `shell=True`). Deleting it leaves a single, coherent implementation.
- Tests covering discovery, command composition, and the edge cases below.

## Non-goals (explicitly out of this slice)

- No `--test-enable` / test execution.
- No `tests/`-folder filtering (install all modules, not just tested ones).
- No `-m <dir>` override and no `git-repos`-based derivation; discovery is
  CWD-only.
- No installation of dependency/localization repos (`sub_*`) or the
  `cl-<client>` definition repo — only the modules found in CWD.
- No installation of extra core/base modules beyond what the project modules
  declare as dependencies (Odoo resolves the dependency chain from `-i`).

## Edge cases

1. **No modules found**: if CWD has no immediate subdirectory containing
   `__manifest__.py`, abort with a clear error (do not run docker, do not
   restore).
2. **Target DB already exists**: if `{client}_test` already exists, prompt the
   user for confirmation before overwriting it (the restore recreates the DB).
   On a negative answer or a non-interactive context, abort without changes.

## Affected modules

| File | Change |
| --- | --- |
| `odoo_env/oe.py` | Fix `--create-test-db` help text (currently "Create database with demo data."). |
| `odoo_env/odooenv.py` | Replace `msg.err` dispatch with a `create_test_db()` method that composes restore + install commands. |
| `odoo_env/managers/environment_manager.py` | Add an install (`-i`) variant of the update docker-run builder; add CWD module-discovery helper (or place discovery where it fits best — decided in design). |
| `odoo_env/create_database.py` | **Deleted** — dead, unreferenced, broken legacy implementation. |
| `odoo_env/test_*.py` | New unit tests (discovery, command composition, edge cases). |

`odoo_env/managers/backup_manager.py` is **not** changed (copy-up approach keeps
the restore contract intact).

Per project rule, prefer extending the `Command` subclass pattern
(`odoo_env/command.py`) over ad-hoc subprocess calls.

## Rollback plan

This is an additive behavior change. To roll back:

- Revert `OdooEnv.create_test_db()` and restore the original
  `msg.err("create-test-db is not yet implemented.")` dispatch in
  `build_commands()`.
- Revert the `environment_manager.py` install variant and discovery helper.
- Revert the `oe.py` help-text change.
- Restore `odoo_env/create_database.py` from git history if its removal ever
  needs to be undone (it has no callers, so this is informational only).

No data migrations, no config schema changes, no changes to the restore
contract — so rollback is a clean code revert. The only runtime side effect is
the `{client}_test` database, which is a throwaway test DB by definition.

## Review workload

Estimated change is small and composition-first (reusing restore and the
docker-run builder), expected well under the 400-line review budget → single PR.

## Next phase

Proceed to **spec** (delta requirements with Given/When/Then scenarios and RFC
2119 keywords) covering: module discovery, seed restore, install, and the two
edge cases.
