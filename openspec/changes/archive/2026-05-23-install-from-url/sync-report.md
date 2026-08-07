# Sync Report: install-from-url

**Status**: ✅ COMPLETE
**Date**: 2026-05-23
**Sync type**: archive-time (no prior sdd-sync run; approved by parent task)

## Domains Synced

| Domain | Canonical Path | Operation | Requirements |
|--------|---------------|-----------|-------------|
| `client` | `openspec/specs/client/spec.md` | New canonical (full copy) | 7 ADDED |
| `test_oe` | `openspec/specs/test_oe/spec.md` | New canonical (full copy) | 6 ADDED |

## Requirement Details

### client — 7 ADDED

| Requirement | Level |
|-------------|-------|
| REQ-INSTALL-001 — Boolean guard for get_manifest | MUST |
| REQ-INSTALL-002 — URL string forwarding to get_manifest_from_url | MUST |
| REQ-INSTALL-003 — URL validation in get_manifest_from_url | MUST |
| REQ-INSTALL-004 — Save client_path on successful URL-based resolution | SHOULD |
| REQ-INSTALL-005 — First-install-only guard | MUST |
| REQ-INSTALL-006 — Temp directory cleanup | MUST |
| REQ-INSTALL-007 — Existing project skip | MUST |

### test_oe — 6 ADDED

| Requirement | Level |
|-------------|-------|
| TEST-INSTALL-001 — Boolean guard: True does not trigger URL clone | MUST |
| TEST-INSTALL-002 — URL string triggers get_manifest_from_url | MUST |
| TEST-INSTALL-003 — Invalid URL raises OeError | MUST |
| TEST-INSTALL-004 — client_path saved after successful URL resolution | MUST |
| TEST-INSTALL-005 — Existing client_path skips URL resolution | MUST |
| TEST-INSTALL-006 — All existing tests continue to pass | MUST |

## Destructive Merge

None. Both domains were new canonicals with no existing specs. No MODIFIED or REMOVED operations.

## Active Same-Domain Change Warnings

None. No other active changes under `openspec/changes/*/specs/` touch `client` or `test_oe` domains.

## Verification

Canonical copies are byte-identical to change specs (verified via `diff`).
