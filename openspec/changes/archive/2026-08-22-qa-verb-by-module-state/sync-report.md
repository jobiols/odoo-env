# Sync Report: qa-verb-by-module-state

**Status**: ✅ COMPLETE
**Date**: 2026-08-22
**Sync type**: archive-time sync fallback — full copy of change spec into a NEW canonical domain `openspec/specs/qa-verb/spec.md`

## Domains Synced

| Domain | Canonical Path | Operation | Requirements |
|--------|---------------|-----------|-------------|
| `qa-verb` | `openspec/specs/qa-verb/spec.md` | New canonical spec (full copy) | 6 ADDED (REQ-QAV-001 .. REQ-QAV-006) |

## Requirement Details

### qa-verb (new canonical domain)

| Requirement | Operation | Level |
|-------------|-----------|-------|
| REQ-QAV-001 — Not-installed module runs with the install verb (`-i`) | ADDED | MUST |
| REQ-QAV-002 — Installed module re-runs its tests with the update verb (`-u`) | ADDED | MUST |
| REQ-QAV-003 — Mixed set produces a single command carrying both verbs | ADDED | MUST |
| REQ-QAV-004 — Module install state resolved via a safe psql query and Python partitioning | ADDED | MUST |
| REQ-QAV-005 — Guard: missing test database aborts | ADDED | MUST |
| REQ-QAV-006 — Guard: requested module not on disk aborts | ADDED | MUST |

## Destructive Merge Guard

Not triggered. This is a brand-new canonical domain (`qa-verb`); no existing
`openspec/specs/qa-verb/spec.md` was present, so there are no REMOVED or MODIFIED
requirement blocks and no removed/replaced line count. The change spec was copied
wholesale (verified byte-identical via `diff`).

## Active Same-Domain Change Warnings

None. `qa-verb` is a new domain; no other active change under `openspec/changes/*`
touches `specs/qa-verb/spec.md`.

## Notes

- This sync was performed at archive time (archive-time sync fallback) because no
  standalone `sdd-sync` had been run for this change. The canonical merge is a pure
  new-domain copy and is non-destructive.
- Canonical spec verified byte-identical to the change spec after copy.
- Verification: 279 tests pass, 0 regressions (see `verify-report.md`).
