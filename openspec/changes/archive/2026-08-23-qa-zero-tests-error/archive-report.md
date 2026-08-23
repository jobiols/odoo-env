# Archive Report: qa-zero-tests-error

**Status**: ✅ PASS — archived
**Date**: 2026-08-23
**Executor**: sdd-archive (parent-orchestrated)
**Artifact store**: OpenSpec (authoritative)

---

## Executive Summary

Archived the `qa-zero-tests-error` change (GitHub issue #128, Part B). `oe -Q <modules>`
now **judges** the Odoo test run instead of trusting Odoo's exit code: it streams the
docker output through a pseudo-terminal (pty), reuses the proven `is_error_line` failure
detector, and adds a new `parse_test_count` parser that aborts on a real failure line, a
non-zero exit, or a "0 tests collected" condition (when at least one requested module has a
`tests/` directory). Odoo's false greens (tests FAIL/ERROR but exit 0, and modules with a
`tests/` dir collecting 0 tests) are now explicit errors.

- Tests: baseline 279 → final **306 OK, 0 regressions** (+27 new tests).
- Verify: **PASS** (valid `gentle-ai.verify-result/v1` envelope, 7/7 requirements, 17/17
  scenarios, test/build exit 0).
- All 16 implementation task boxes checked `[x]`; no unchecked `- [ ]` markers.
- Part A (`qa-verb-by-module-state`) is already merged/archived (commit `1aad9f1`); this
  Part B completes the remaining half of #128 but does **NOT** close it (the user closes the
  issue after the manual REQ-QAJ-006 real-run check + merge).

---

## Artifacts Read

| Artifact | Path | Status |
|----------|------|--------|
| Proposal | `proposal.md` | ✅ |
| Spec (qa-judgement) | `specs/qa-judgement/spec.md` | ✅ 7 requirements (REQ-QAJ-001 .. 007), 17 scenarios |
| Design | `design.md` | ✅ (ADR-1 .. ADR-6) |
| Tasks | `tasks.md` | ✅ 16/16 `[x]` |
| Apply Progress | `apply-progress.md` | ✅ |
| Verify Report | `verify-report.md` | ✅ PASS (envelope verdict `pass`) |
| Sync Report | `sync-report.md` | N/A — none present; consolidation performed at archive time (see below) |
| Config | `openspec/config.yaml` | ✅ read |

## Final Task Completion Gate

Re-read `tasks.md` immediately before sync/move. Result: **16 `[x]` task markers, zero
`- [ ]` markers** (grep for `^\s*- \[ \]` returned none). No stale-checkbox reconciliation
was required — apply-progress and verify-report both confirm all 16 implementation tasks were
marked complete by `sdd-apply`.

## Spec Consolidation / Sync

| Domain | Canonical Path | Operation | Requirements |
|--------|---------------|-----------|-------------|
| `qa-judgement` | `openspec/specs/qa-judgement/spec.md` | New canonical domain (full copy) | 7 ADDED |

- **ADDED:** REQ-QAJ-001, REQ-QAJ-002, REQ-QAJ-003, REQ-QAJ-004, REQ-QAJ-005, REQ-QAJ-006,
  REQ-QAJ-007.
- **MODIFIED:** none. **REMOVED:** none.
- New canonical spec verified byte-identical to the change spec (`diff` clean).
- **Destructive merge guard:** NOT triggered — brand-new domain, no existing canonical spec,
  no removals/replacements, no removed-line count.
- **Active same-domain warnings:** none (`qa-judgement` is a new domain; no other active change
  touches it).
- **Archive-time sync fallback:** no `sync-report.md` existed in this change; the parent
  orchestrator explicitly authorized archive-time consolidation as a full copy into the new
  canonical domain (non-destructive).

## Structured Status / ActionContext Findings

- `schemaName`: spec-driven
- `artifactStore`: openspec (authoritative; `openspec/` present)
- `actionContext`: repo-local; source edits confined to `odoo_env/` + `doc/uml/` under
  `/home/jobiols/tmp/odoo-env`
- `dependencies.apply`: all_done; `dependencies.verify`: all_done; `dependencies.archive`: ready
- `taskProgress`: 16/16 complete (all `[x]`)
- No `blockedReasons`; no edit-authority concern. Whole repo editable at
  `/home/jobiols/tmp/odoo-env`.

## Verification Evidence

- Command: `PYTHONPATH=. python3 -m unittest discover -s odoo_env -p "test_*.py"` → **306 OK**.
- Verify-report envelope: `schema: gentle-ai.verify-result/v1`, `verdict: pass`,
  `blockers: 0`, `critical_findings: 0`, `requirements: 7/7`, `scenarios: 17/17`,
  `test_exit_code: 0`, `build_exit_code: 0`.
- CRITICAL verification issues: **none**. No archive blockers.

## Final-State Facts (outrank apply-progress / verify-report snapshots)

Work completed AFTER `verify-report.md` was persisted (by the orchestrator, this session):

- **pre-commit fixes (3 pylint failures resolved):**
  1. `command.py` R1732 consider-using-with: the PTY seam (`pty.openpty` + `subprocess.Popen`)
     is intentionally `with`-free because `TestPtySeam` patches exactly
     `os.read`/`os.close`/`Popen`. Fixed with a block-level
     `# pylint: disable=consider-using-with` + explanatory comment in `_stream_lines`.
  2. `test_create_test_db.py` C0302 too-many-lines (was 1057 lines): split the 5 `QaCommand`
     test classes into a NEW file `odoo_env/test_qa_command.py` (272 lines).
     `test_create_test_db.py` is now 792 lines.
  3. `test_create_test_db.py` W0613 unused-argument: replaced the `fake_stream` closure with
     `cmd._stream_lines = MagicMock(return_value=lines)` (also resolved a Pyright param-name
     mismatch).
- `pre-commit run --all-files` now passes ALL hooks (autoflake, isort, black, pylint, pyreverse).
- `doc/uml/classes_odoo_env.plantuml` + `doc/uml/packages_odoo_env.plantuml` regenerated by
  pyreverse to reflect the new QaCommand/QaVerdict/test classes.
- Full suite: **306 tests OK** (baseline 279, +27).
- `verify-report.md` envelope was UPDATED with fresh post-fix hashes:
  `evidence_revision sha256:17e06e0164f4143aa777c505b53b82e738dfd7d6ed8c5856814cb3d476a656f3`,
  `test_output_hash sha256:b2e8ec37579773baa391c517ccc52ed3a5cae911f5c4d8b9a6a5d7f33a93a4be`.
  Envelope re-validated (`sdd-verify-validate --requirements 7 --scenarios 17` → valid:true,
  verdict pass).
- **NOT committed** — the user owns all commits (implementation + archive + a separate
  `openspec/config.yaml` fix). Archive does NOT commit.

## Deferred Follow-ups (recorded, not part of this change)

1. **REQ-QAJ-006 (ANSI colors + no staircase) — MANUAL-DEFERRED.** Requires a real
   `oe -Q <module_with_colored_failing_test>` Docker run before merge; checklist documented in
   the `_stream_lines` docstring. Not unit-testable (no real pty/Docker in unittest).
2. **Pre-existing findings NOT introduced by this change:**
   - `command.py` `subprocess_call` unreachable-except (identical to HEAD).
   - `odoo_env/data/nginx.key` real RSA key tracked since 2019 (gitleaks/opengrep flag — out of
     scope; user decides rotation/removal).
3. **Issue #128 not closed by this change** — Part B completes the remaining half; the user
   closes the issue after the manual REQ-QAJ-006 check + merge.

## Destructive Merge Approvals / Blockers

None required and none encountered. The canonical consolidation was a non-destructive full copy
into a new domain.

## Archived Path

`openspec/changes/qa-zero-tests-error/` → `openspec/changes/archive/2026-08-23-qa-zero-tests-error/`

Naming follows the project's established dated convention (matching
`2026-08-22-qa-verb-by-module-state`, `2026-06-14-qa-coverage-ci`, etc.). The change uses the
`specs/{domain}/spec.md` structure, so the dated prefix was applied per the convention.

## Memory Observation IDs

N/A — OpenSpec-only artifact store (file-backed). No Engram observation written (archive report
lives in the file backend).

## Notes

- No commit performed; the user owns the follow-up commits (implementation, archive, config fix).
- Audit trail preserved: archived change directory was moved, never deleted.
- `openspec/config.yaml` remains modified in the working tree (pre-existing venv→python3 test
  command fix) and is intentionally left for a separate user commit.
