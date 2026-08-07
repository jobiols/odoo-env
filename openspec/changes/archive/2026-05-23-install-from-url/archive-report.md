# Archive Report: install-from-url

**Status**: ✅ PASS
**Date**: 2026-05-23
**Executor**: sdd-archive (archive-time sync fallback, parent-approved)

---

## Executive Summary

Archived the `install-from-url` change — a bug fix for the `oe -i` crash when `-i` is passed without a URL. All phases complete: explore, proposal, spec, design, tasks, apply, verify, sync, archive. 92/92 tests pass, zero regressions, ~238 lines total delta (~8 implementation, ~230 test).

---

## Artifacts Read

| Artifact | Path | Status |
|----------|------|--------|
| Proposal | `openspec/changes/install-from-url/proposal.md` | ✅ Read |
| Spec (client) | `openspec/changes/install-from-url/specs/client/spec.md` | ✅ Read — 7 requirements, 12 scenarios |
| Spec (test_oe) | `openspec/changes/install-from-url/specs/test_oe/spec.md` | ✅ Read — 6 requirements, 6 scenarios |
| Design | `openspec/changes/install-from-url/design.md` | ✅ Read — 6 ADRs |
| Tasks | `openspec/changes/install-from-url/tasks.md` | ✅ Read — 10 tasks, all ✅ COMPLETE |
| Verify Report | `openspec/changes/install-from-url/verify-report.md` | ✅ Read — PASS with advisory findings |
| Sync Report | `openspec/changes/install-from-url/sync-report.md` | ✅ Written (archive-time sync) |
| Apply Progress | `openspec/changes/install-from-url/apply-progress.md` | ✅ Read |
| Config | `openspec/config.yaml` | ✅ Read — rules.archive: warn before destructive merges |

---

## Sync Summary

Archive-time sync (parent explicitly approved as part of task: "Move specs to canonical domain specs").

| Domain | Operation | Requirements |
|--------|-----------|-------------|
| `client` | New canonical (full copy → `openspec/specs/client/spec.md`) | 7 ADDED |
| `test_oe` | New canonical (full copy → `openspec/specs/test_oe/spec.md`) | 6 ADDED |

### ADDED Requirements

**client domain** (7 requirements):
- REQ-INSTALL-001 — Boolean guard for get_manifest (MUST)
- REQ-INSTALL-002 — URL string forwarding to get_manifest_from_url (MUST)
- REQ-INSTALL-003 — URL validation in get_manifest_from_url (MUST)
- REQ-INSTALL-004 — Save client_path on successful URL-based resolution (SHOULD)
- REQ-INSTALL-005 — First-install-only guard (MUST)
- REQ-INSTALL-006 — Temp directory cleanup (MUST)
- REQ-INSTALL-007 — Existing project skip (MUST)

**test_oe domain** (6 requirements):
- TEST-INSTALL-001 through TEST-INSTALL-006 (all MUST)

### MODIFIED Requirements

None.

### REMOVED Requirements

None.

### Destructive Merge

None. Both domains were new canonicals — no existing specs to modify or remove.

### Active Same-Domain Warnings

None. No other active changes under `openspec/changes/*/specs/` touch `client` or `test_oe` domains.

---

## Verify Report Summary

| Criterion | Result |
|-----------|--------|
| All 92 tests pass | ✅ |
| Zero regressions | ✅ |
| All MUST requirements met | ✅ |
| All SHOULD requirements met | ✅ |
| Strict TDD compliance | ✅ |
| Assertion quality | ✅ No weak assertions |
| Review workload within budget | ✅ 238 < 400 |
| No scope creep | ✅ |
| Rollback safe | ✅ |
| Blockers | None |

### Advisory Findings

| Finding | Severity | Status |
|---------|----------|--------|
| F-001: Dead temp path saved to config | ADVISORY | Acknowledged (ADR-002 design trade-off) |
| F-002: No explicit temp-cleanup assertion | MINOR | Acknowledged (context manager guarantee) |
| F-003: Empty URL test doesn't verify URL in message | COSMETIC | Acknowledged |

No FAIL, BLOCKED, or CRITICAL findings. All findings are informational.

---

## Implementation Summary

### Files Modified

| File | Change | Lines |
|------|--------|-------|
| `odoo_env/client.py` | 3 changes: isinstance guard (line 192), URL validation (lines 136-138), save_client_path (lines 145-147) | ~8 |
| `odoo_env/test_client.py` | NEW: 10 test methods, setUp/tearDown mocks | ~230 |

### Git Status (uncommitted, by design)

```
 M odoo_env/client.py
?? .pi-lens/
?? odoo_env/test_client.py
?? openspec/changes/install-from-url/
```

### Key Change

```python
# client.py:192 — The fix
-            if self._args.install:
+            if isinstance(self._args.install, str):
```

Boolean `True` (no-URL `-i`) no longer triggers `get_manifest_from_url()`.

---

## Archived Path

```
openspec/changes/install-from-url/
  → openspec/changes/archive/2026-05-23-install-from-url/
```

---

## Memory / Engram

Engram memory tools are not available in this session (per SDD preflight: `artifact store: openspec (Engram unavailable in this session)`). The requested topic key `sdd/install-from-url/archive-report` cannot be persisted. The archive report is available at:

- **File**: `openspec/changes/archive/2026-05-23-install-from-url/archive-report.md`
- **Canonical specs**: `openspec/specs/client/spec.md`, `openspec/specs/test_oe/spec.md`

---

## Change Lifecycle Summary

| Phase | Status | Artifacts |
|-------|--------|-----------|
| Explore | ✅ Complete | Root cause: `isinstance` bug + 4 issues |
| Proposal | ✅ Complete | `proposal.md` — approved fix strategy |
| Spec | ✅ Complete | `specs/client/spec.md` (7 reqs, 12 scenarios), `specs/test_oe/spec.md` (6 reqs) |
| Design | ✅ Complete | `design.md` — 6 ADRs |
| Tasks | ✅ Complete | `tasks.md` — 10 tasks across 4 TDD phases |
| Apply | ✅ Complete | 3 code changes, 10 new tests, RED→GREEN→VERIFY |
| Verify | ✅ Complete | `verify-report.md` — PASS, 92/92 tests, zero regressions |
| Sync | ✅ Complete (archive-time) | `sync-report.md` — 2 domains, 13 requirements ADDED |
| Archive | ✅ Complete | `archive-report.md` — moved to `archive/2026-05-23-install-from-url/` |

---

## Rollback

All changes are additive/single-line replacements. Rollback is `git revert` of the change commit. No config format changes, no database, no migration.
