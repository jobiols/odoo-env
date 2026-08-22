# Archive Report: qa-verb-by-module-state

**Status**: ✅ PASS — archived
**Date**: 2026-08-22
**Executor**: sdd-archive (parent-orchestrated)
**Artifact store**: OpenSpec (authoritative)

---

## Executive Summary

Archived the `qa-verb-by-module-state` change (GitHub issue #128, Part A). `oe -Q <modules>`
now selects the Odoo verb per module according to its real install state in the
`<client>_test` database: not-installed modules use `-i` (their tests actually run), and
already-installed modules use `-u` (tests re-run). A mixed set produces a single dual-verb
command. Two fail-loud guards were added (missing test DB, unknown module on disk).

- Commit `1aad9f1` "fix(qa): select Odoo verb per module install state in oe -Q" pushed to
  `master`; `refs #128` (issue intentionally NOT closed — Part B deferred).
- Tests: baseline 261 → final **279 OK, 0 regressions** (+18 new tests).
- Verify: **PASS** (valid `gentle-ai.verify-result/v1` envelope, 6/6 requirements, 13/13
  scenarios, test/build exit 0).
- All 13 implementation task boxes checked `[x]`; no unchecked `- [ ]` markers.

---

## Artifacts Read

| Artifact | Path | Status |
|----------|------|--------|
| Proposal | `proposal.md` | ✅ |
| Spec (qa-verb) | `specs/qa-verb/spec.md` | ✅ 6 requirements (REQ-QAV-001 .. 006), 13 scenarios |
| Design | `design.md` | ✅ (ADR-1 .. ADR-5) |
| Tasks | `tasks.md` | ✅ 13/13 `[x]` |
| Apply Progress | `apply-progress.md` | ✅ |
| Verify Report | `verify-report.md` | ✅ PASS (envelope verdict `pass`) |
| Sync Report | `sync-report.md` | ✅ written at archive time |
| Config | `openspec/config.yaml` | ✅ read |

## Final Task Completion Gate

Re-read `tasks.md` immediately before sync/move. Result: **13 `[x]` task markers, zero
`- [ ]` markers** (grep for `^\s*- \[ \]` returned none). No stale-checkbox reconciliation
was required — apply-progress and verify-report both confirm all implementation tasks were
marked complete by `sdd-apply`.

## Spec Consolidation / Sync

| Domain | Canonical Path | Operation | Requirements |
|--------|---------------|-----------|-------------|
| `qa-verb` | `openspec/specs/qa-verb/spec.md` | New canonical domain (full copy) | 6 ADDED |

- **ADDED:** REQ-QAV-001, REQ-QAV-002, REQ-QAV-003, REQ-QAV-004, REQ-QAV-005, REQ-QAV-006.
- **MODIFIED:** none. **REMOVED:** none.
- New canonical spec verified byte-identical to the change spec (`diff` clean).
- **Destructive merge guard:** NOT triggered — brand-new domain, no existing canonical spec,
  no removals/replacements, no removed-line count.
- **Active same-domain warnings:** none (`qa-verb` is a new domain; no other active change
  touches it).

## Structured Status / ActionContext Findings

- `schemaName`: spec-driven
- `artifactStore`: openspec (authoritative; `openspec/` present)
- `actionContext`: repo-local; source edits confined to `odoo_env/` under
  `/home/jobiols/tmp/odoo-env`
- `dependencies.archive`: ready; `dependencies.verify`: all_done
- No `blockedReasons`; no edit-authority concern (implementation already committed by user).

## Verification Evidence

- Command: `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"` → **279 OK**.
- Verify-report envelope: `schema: gentle-ai.verify-result/v1`, `verdict: pass`,
  `blockers: 0`, `requirements: 6/6`, `scenarios: 13/13`, `test_exit_code: 0`,
  `build_exit_code: 0`.
- CRITICAL verification issues: **none**. No archive blockers.

## Final-State Facts (outrank apply-progress / verify-report snapshots)

- Implementation committed and pushed to `master` (commit `1aad9f1`).
- **Uncommitted changes exist** beyond that commit and are intentionally left for the user
  to commit: `verify-report.md` (now carries the valid envelope) and a small refactor in
  `test_environment_manager.py` (two `qa()` calls switched to keyword arguments for clarity
  and to clear a stale LSP cache). The OpenSpec artifacts + these two files need a follow-up
  commit by the user — archive does NOT commit.

## Deferred Follow-ups (recorded, not part of this change)

1. **Part B** — turn "0 tests collected on a module with a `tests/` dir" into an explicit
   ERROR. Requires a streaming + output-parsing execution model and a new `of (\d+) tests`
   parse. Separate future change.
2. **Config defect** — `openspec/config.yaml` `testing.test_runner.command` references
   `venv/bin/python`, which does not exist; the real runner is system `python3`. Follow-up
   config fix.
3. **CI path divergence (documented, not unified)** — `odoo_env/qa/runner.py` still uses a
   fixed `-i` verb, which is correct only because the CI path restores a fresh seed test DB
   on each run. Documented divergence from the per-state `oe -Q` strategy.

## Destructive Merge Approvals / Blockers

None required and none encountered. The canonical sync was a non-destructive full copy into a
new domain.

## Archived Path

`openspec/changes/qa-verb-by-module-state/` → `openspec/changes/archive/2026-08-22-qa-verb-by-module-state/`

Naming follows the project's established dated convention (matching `2026-06-14-qa-coverage-ci`,
`2026-06-15-install-by-client-name`, etc.). The change uses the `specs/{domain}/spec.md`
structure, so the dated prefix was applied per the convention rather than the legacy un-dated
flat-layout names.

## Memory Observation IDs

N/A — OpenSpec-only artifact store (file-backed). No Engram observation written.

## Notes

- No commit performed; the user owns the follow-up commit.
- Audit trail preserved: archived change directory was moved, never deleted.
