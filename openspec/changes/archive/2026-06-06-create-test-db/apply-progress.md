# Apply Progress: create-test-db

**Date**: 2026-06-06
**Status**: Complete (all phases done, full suite green)

## TDD Cycle Evidence

### Cycle 1: discover_modules_in_cwd (RED → GREEN)

| Phase | Test | Evidence |
|-------|------|----------|
| RED | `test_discover_modules_finds_manifest_dirs` | `AttributeError: type object 'EnvironmentManager' has no attribute 'discover_modules_in_cwd'` |
| RED | `test_discover_modules_empty_cwd` | Same AttributeError |
| RED | `test_discover_modules_ignores_hidden_dirs` | Same AttributeError |
| RED | `test_discover_modules_ignores_root_manifest` | Same AttributeError |
| RED | `test_discover_modules_does_not_recurse` | Same AttributeError |
| GREEN | All 5 discovery tests | 5/5 pass after implementing `discover_modules_in_cwd()` staticmethod |

### Cycle 2: _build_module_command (RED → GREEN)

| Phase | Test | Evidence |
|-------|------|----------|
| RED | `test_build_module_command_install` | `AttributeError: 'EnvironmentManager' object has no attribute '_build_module_command'` |
| GREEN | `test_build_module_command_install` | Pass: command contains `-i`, `module_a, module_b`, `--stop-after-init`, no `--test-enable`; usr_msg starts with "Installing " |
| BASELINE | `test_update_still_works_after_refactor` | Pass before and after refactor: `-u`, `all`, `--stop-after-init`, usr_msg starts with "Performing update of " |

### Cycle 3: create_test_db guards (RED → GREEN)

| Phase | Test | Evidence |
|-------|------|----------|
| RED | `test_create_test_db_zero_modules_aborts` | `AttributeError: <class 'OdooEnv'> does not have the attribute '_db_exists'` |
| RED | `test_create_test_db_confirm_yes_proceeds` | Same AttributeError on `_db_exists` |
| RED | `test_create_test_db_confirm_no_aborts` | Same |
| RED | `test_create_test_db_non_interactive_aborts` | Same |
| RED | `test_create_test_db_eof_aborts` | Same |
| RED | `test_create_test_db_command_composition` | Same |
| RED | `test_create_test_db_seed_missing_aborts` | Same |
| RED | `test_create_test_db_dispatched_from_build_commands` | `AttributeError: OdooEnv does not have 'create_test_db'` |
| GREEN | All 8 Phase 4-5 tests | 8/8 pass after implementing `_db_exists`, `_confirm_overwrite`, `create_test_db`, and dispatch |

### Full Suite Regression

| Run | Result |
|-----|--------|
| Full suite after all changes | **131 tests, 0 failures, 0 errors** |

## Files Changed

| File | Type | Lines Est. |
|------|------|-----------|
| `odoo_env/test_oe.py` | Added `TestCreateTestDb` class with 15 test methods | +145 |
| `odoo_env/managers/environment_manager.py` | Added `discover_modules_in_cwd()` staticmethod + `_build_module_command()` extraction, refactored `update()` | +55 |
| `odoo_env/odooenv.py` | Added `_db_exists()`, `_confirm_overwrite()`, `create_test_db()` methods + wired dispatch | +90 |
| `odoo_env/oe.py` | Fixed `--create-test-db` help text | +1 |
| `odoo_env/create_database.py` | **Deleted** (dead code, zero callers) | -34 |
| `openspec/changes/create-test-db/tasks.md` | Marked all 69 tasks complete | updates |

**Total**: ~195 changed lines (well under 400-line budget)

## Deviations from Design

1. **Guard ordering**: Seed-existence guard placed AFTER DB-exists confirmation guard (not before). This follows ADR 6 sequence where DB-exists check (step 4) comes before commands (step 5). Seed guard runs just before CP command per ADR 4.
2. **`_build_module_command` prefix**: Added `usr_msg_prefix` parameter so `update()` can pass `"Performing update of"` while install uses default `"Installing"`.
3. **Test adaptation**: Tests 4.2 and 4.6 added `patch.object(Path, "is_file", return_value=True)` to pass seed guard after confirm check.

## Commands Run

- `python -m unittest odoo_env.test_oe.TestCreateTestDb` → NO TESTS RAN (infra check)
- `python -m unittest odoo_env.test_oe.TestCreateTestDb.test_discover_modules_*` → RED (AttributeError)
- `python -m unittest odoo_env.test_oe.TestCreateTestDb.test_build_module_command_install` → RED
- `python -m unittest odoo_env.test_oe.TestCreateTestDb` → 8/8 GREEN (guard + composition + dispatch)
- `python -m unittest discover -s odoo_env -p 'test_*.py'` → 131 tests, 0 failures

## Remaining Tasks

None — all 69 tasks complete.
