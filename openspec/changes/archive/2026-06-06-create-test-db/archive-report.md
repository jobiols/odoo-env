# Archive Report: create-test-db

**Status**: ✅ PASS
**Date**: 2026-06-06
**Executor**: sdd-archive

---

## Executive Summary

Archived the `create-test-db` change — a new CLI action (`oe --create-test-db`) that discovers Odoo modules in the current working directory, copies a seed backup, restores it into a `{client}_test` database, installs all discovered modules with `-i`, and cleans up. All 7 SDD phases complete: explore, proposal, spec, design, tasks, apply, verify, sync, archive. 131/131 tests pass (15 new, 116 pre-existing), zero failures, zero errors, zero regressions. Dead code (`create_database.py`) removed with zero remaining references. ~377 net productive lines (~339 added, -38 removed).

---

## Artifacts Read

| Artifact | Path | Status |
|----------|------|--------|
| Proposal | `openspec/changes/create-test-db/proposal.md` | ✅ Read — 2 objectives, scope, rollback |
| Spec (create-test-db) | `openspec/changes/create-test-db/specs/create-test-db/spec.md` | ✅ Read — 7 requirements, 20 scenarios |
| Design | `openspec/changes/create-test-db/design.md` | ✅ Read — 7 ADRs |
| Tasks | `openspec/changes/create-test-db/tasks.md` | ✅ Read — 69 tasks, all ✅ COMPLETE (0 unchecked) |
| Verify Report | `openspec/changes/create-test-db/verify-report.md` | ✅ Read — PASS, 0 CRITICAL, 0 WARNING |
| Apply Progress | `openspec/changes/create-test-db/apply-progress.md` | ✅ Read — 3 TDD cycles, all GREEN |
| Sync Report | `openspec/changes/create-test-db/sync-report.md` | ✅ Read — SYNCED, new-domain promotion |
| Explore Report | `openspec/changes/create-test-db/explore-report.md` | ✅ Read |
| Config | `openspec/config.yaml` | ✅ Read — rules.archive: warn before destructive merges |

---

## Sync Summary

Pre-archive sync (performed by `sdd-sync` before `sdd-archive`).

| Domain | Operation | Requirements |
|--------|-----------|-------------|
| `create-test-db` | New canonical (full copy → `openspec/specs/create-test-db/spec.md`) | 7 ADDED |

### ADDED Requirements

**create-test-db domain** (7 requirements, all MUST):

| Requirement | Description |
|-------------|-------------|
| REQ-CTDB-001 | Command trigger and database naming (`{client}_test`) |
| REQ-CTDB-002 | Module discovery (CWD only, all modules with `__manifest__.py`) |
| REQ-CTDB-003 | Seed restore via copy-up (cp → restore → rm sequence) |
| REQ-CTDB-004 | Module install with `-i` and no `--test-enable` |
| REQ-CTDB-005 | Edge case: zero modules aborts before restore |
| REQ-CTDB-006 | Edge case: existing database confirmation (interactive/non-interactive/EOFError) |
| REQ-CTDB-007 | Order of operations (guards before build, restore before install) |

### MODIFIED Requirements

None.

### REMOVED Requirements

None.

### Destructive Merge

None. `create-test-db` is a new domain with no prior canonical spec. The promotion was a byte-identical full copy of the verified delta spec. No MODIFIED or REMOVED operations. `config.yaml` rule `archive: warn before merging destructive deltas` was evaluated — no warning required.

### Active Same-Domain Warnings

None. No other active changes under `openspec/changes/*/specs/` touch the `create-test-db` domain. Existing canonical domains (`client`, `test_oe`) are unaffected.

---

## Verify Report Summary

| Criterion | Result |
|-----------|--------|
| All 131 tests pass (15 new + 116 pre-existing) | ✅ |
| Zero failures, zero errors | ✅ |
| Zero regressions | ✅ |
| All 7 MUST requirements traced to tests + code | ✅ |
| Strict TDD compliance (3 RED→GREEN cycles) | ✅ |
| Assertion quality (no tautologies, no smoke-only tests) | ✅ |
| Non-requirements verification (6 items clean) | ✅ |
| Dead code removed with zero remaining references | ✅ |
| BackupManager.restore contract unchanged | ✅ |
| Review workload within 400-line budget (~377 lines) | ✅ |
| No scope creep | ✅ |
| Blockers | None |

### Advisory Findings

| Finding | Severity | Status |
|---------|----------|--------|
| SUGGESTION-1: TestCreateTestDb extends unittest.TestCase directly (not OdooEnvTestCase) | INFO | Intentional — no client manifest/config mocking needed |
| SUGGESTION-2: Unreachable `return False` after `msg.err()` in `_confirm_overwrite` | COSMETIC | Correct behavior — exception prevents return from being reached |

No FAIL, BLOCKED, or CRITICAL findings.

---

## Implementation Summary

### Files Modified

| File | Change | Lines |
|------|--------|-------|
| `odoo_env/create_database.py` | DELETED (dead code removal) | -38 |
| `odoo_env/managers/environment_manager.py` | NEW: `discover_modules_in_cwd()` static method + `_build_module_command()` extraction and `update()` refactor | +44 |
| `odoo_env/odooenv.py` | NEW: `create_test_db()`, `_db_exists()`, `_confirm_overwrite()` methods + dispatch wiring in `build_commands()` | +103 |
| `odoo_env/oe.py` | MODIFIED: `--create-test-db` help text update | +2 |
| `odoo_env/test_oe.py` | NEW: 15 test methods (5 discovery + 1 install + 1 regression + 8 create_test_db) | +228 |
| `.vscode/launch.json` | Local dev config (not part of this change) | — |
| **Net productive** | | **~377 lines** |

### Test Count

- **Pre-existing**: 116 (TestRepository: 28, TestGetPacks: 3, TestGetManifest: 10, TestOdooVersionMap: 9, TestDockerClient: 3, TestGetExtractCommand: 4, TestDebugMountings: 19, TestEnvironmentManager: 4, TestImageManager: 10, TestFilterImagesByMask: 10, TestGetImages: 3, TestProcessInputOther: 6, TestProcessInputRmdisk: 4)
- **New**: 15 (TestCreateTestDb: discovery × 5, install × 1, regression × 1, create_test_db guards + composition × 8)
- **Total**: 131 — all PASS

### Key Changes

```python
# odoo_env/managers/environment_manager.py — Module discovery (REQ-CTDB-002)
@staticmethod
def discover_modules_in_cwd():
    """Returns sorted list of immediate subdirectory names in CWD that contain __manifest__.py."""
    ...

# odoo_env/odooenv.py — Main method (REQ-CTDB-001 through 007)
def create_test_db(self):
    modules = EnvironmentManager.discover_modules_in_cwd()
    if not modules: msg.err("No Odoo modules found...")      # REQ-CTDB-005
    database = f"{self.client.name}_test"                     # REQ-CTDB-001
    # Guard: DB exists → confirm overwrite                    # REQ-CTDB-006
    # Guard: seed file exists                                  # ADR 4
    # Build: cp seed → restore(no_deactivate=True) → rm → -i  # REQ-CTDB-003, 004, 007
    ...

# odoo_env/create_database.py — DELETED (dead code, zero callers)
```

### Git Status (uncommitted, by design)

```
 M odoo_env/oe.py
 M odoo_env/managers/environment_manager.py
 M odoo_env/odooenv.py
 D odoo_env/create_database.py
 M odoo_env/test_oe.py
?? openspec/changes/create-test-db/
```

---

## Archived Path

```
openspec/changes/create-test-db/
  → openspec/changes/archive/2026-06-06-create-test-db/
```

Canonical spec remains at:

```
openspec/specs/create-test-db/spec.md
```

---

## Memory / Engram

Engram memory tools are not available in this session (per SDD preflight: `artifact store: openspec (Engram unavailable in this session)`). The archive report is available at:

- **File**: `openspec/changes/archive/2026-06-06-create-test-db/archive-report.md`
- **Canonical spec**: `openspec/specs/create-test-db/spec.md`

---

## Change Lifecycle Summary

| Phase | Status | Artifacts |
|-------|--------|-----------|
| Explore | ✅ Complete | `explore-report.md` — codebase survey, existing patterns |
| Proposal | ✅ Complete | `proposal.md` — 2 objectives, approved scope |
| Spec | ✅ Complete | `specs/create-test-db/spec.md` — 7 requirements (REQ-CTDB-001 through 007), 20 scenarios |
| Design | ✅ Complete | `design.md` — 7 ADRs |
| Tasks | ✅ Complete | `tasks.md` — 69 tasks across 7 phases |
| Apply | ✅ Complete | 3 TDD cycles (RED→GREEN→REFACTOR), all 69 tasks complete |
| Verify | ✅ Complete | `verify-report.md` — PASS, 131/131 tests, 0 CRITICAL, 0 WARNING |
| Sync | ✅ Complete | `sync-report.md` — 1 domain, 7 requirements ADDED |
| Archive | ✅ Complete | `archive-report.md` — moved to `archive/2026-06-06-create-test-db/` |

---

## Rollback

All changes are additive or deletion-only. The main implementation is a new `create_test_db()` method in `odooenv.py` called only from `build_commands()` when `--create-test-db` is passed. Rollback is `git revert` of the change commit. No config format changes, no database migration, no API contract changes. `BackupManager.restore` contract is unchanged (same signature, new call site with `no_deactivate=True`).
