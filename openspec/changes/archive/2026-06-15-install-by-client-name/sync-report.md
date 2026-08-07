# Sync Report: install-by-client-name

**Status**: ✅ COMPLETE
**Date**: 2026-06-15
**Sync type**: full copy of change spec into canonical `openspec/specs/client/spec.md`

## Domains Synced

| Domain | Canonical Path | Operation | Requirements |
|--------|---------------|-----------|-------------|
| `client` | `openspec/specs/client/spec.md` | Updated canonical (full copy) | 1 MODIFIED, 3 ADDED, 6 unchanged |

## Requirement Details

### client

| Requirement | Operation | Level |
|-------------|-----------|-------|
| REQ-INSTALL-001 — Boolean guard for get_manifest | unchanged | MUST |
| REQ-INSTALL-002 — URL string forwarding (+ bare-name scenario) | scenario added | MUST |
| REQ-INSTALL-003 — Input resolution and validation in get_manifest_from_url | MODIFIED | MUST |
| REQ-INSTALL-004 — Save client_path on successful URL-based resolution | unchanged | SHOULD |
| REQ-INSTALL-005 — First-install-only guard | unchanged | MUST |
| REQ-INSTALL-006 — Temp directory cleanup | unchanged | MUST |
| REQ-INSTALL-007 — Existing project skip | unchanged | MUST |
| REQ-INSTALL-008 — Canonical repository URL from client name | ADDED | MUST |
| REQ-INSTALL-009 — Organization configuration | ADDED | MUST |
| REQ-INSTALL-010 — Client-name validation and normalization | ADDED | MUST |

## Notes

- REQ-INSTALL-003 changed meaning: `get_manifest_from_url()` now resolves the install
  input into a URL (full URL verbatim, or bare client name → canonical URL) before
  cloning. A non-URL string like `"not-a-url"` is now a valid client name (builds a
  canonical URL) rather than an error. Only empty strings and names with spaces/`/`
  raise `OeError`.
- Canonical spec verified byte-identical to the change spec after copy.
- Verification: 208 tests pass (see verify-report.md).
