# Apply Progress: qa-coverage-ci

**Strict TDD**: true · **Delivery**: 4 chained PRs · **Branch**: master.impruve-r

## PR1 — foundational modules ✅ (complete, not yet committed)

Phases 1–4 of tasks.md.

| File | Status |
|------|--------|
| `odoo_env/qa/__init__.py` | added |
| `odoo_env/qa/failures.py` | added — `is_error_line` (ANSI strip + `: FAIL:/: ERROR:` match, ADR 4) |
| `odoo_env/qa/config.py` | added — `RunnerConfig` + `from_oe` + `needs_with_demo_flag` (ADR 1, 7) |
| `odoo_env/qa/threshold.py` | added — `read_floor` (default 20, malformed→ValueError, range 0–100) + `check_ratchet` (ADR 6) |
| `odoo_env/test_qa.py` | added — 20 unit tests |

**Evidence**: `python -m unittest odoo_env.test_qa` → 20 OK; full suite 165 OK; `pre-commit` (pylint 10/10, black, pyreverse) green.

**Fresh review** (run 968f6048): 1 blocker + 3 majors found and fixed:
- Blocker: `read_floor` crashed on malformed file → now raises a clear `ValueError`; missing file still defaults to 20.
- Removed tautological `resolved_with_demo` property (intent "always demo" belongs to the PR2 runner).
- Added negative/boundary tests: malformed floor, out-of-range floor, `18.0` demo boundary, `ERROR`-without-word.

**Deviation from tasks.md**: dropped `resolved_with_demo` (REQ-QA-008 demo intent now expressed only via `needs_with_demo_flag`); `RunnerConfig.numeric_ver` carries the version for the demo decision.

## PR2 — TestRunner + DockerClient extension ✅ (complete, not yet committed)

Phases 5–6 of tasks.md.

| File | Status |
|------|--------|
| `odoo_env/qa/runner.py` | added — `TestRunner` (discovery, command composition, run_all, report, check_threshold) |
| `odoo_env/test_qa.py` | extended — 22 new tests (DiscoveryTests, CommandCompositionTests, RunAllTests, ReportTests, ThresholdEnforcementTests) |

**Evidence**: `python -m unittest odoo_env.test_qa` → 42 OK (20 PR1 + 22 PR2); full suite 187 OK; `pre-commit` green.

**Fresh review** (run 1ebb63d2): 0 blockers, 1 major + 4 minors fixed:
- Major: fragile `shlex.quote` concatenation (partial path quoted + bare suffix) → now quote full paths (`IN_CONFIG + 'odoo.conf'`, `cov_dir + '/htmlcov'`).
- Added warning on malformed master `.coverage-threshold`.
- Human-friendly prints preserved (no separate quiet flag yet).

**Note**: Minor #3 (KeyboardInterrupt) and Minor #5 (extra volumes) are documented but deferred.

## PR3 — CLI + `oe --test-all` ✅ (complete, not yet committed)

Phase 7 of tasks.md.

| File | Status |
|------|--------|
| `odoo_env/qa/__main__.py` | added — CLI entrypoint (`python -m odoo_env.qa`, resolves Client from oe config, calls TestRunner) |
| `odoo_env/command.py` | extended — `TestAllCommand` (REQ-QA-010) |
| `odoo_env/odooenv.py` | extended — `_build_test_all` dispatcher using `RunnerConfig.from_oe` + `TestRunner` |
| `odoo_env/oe.py` | extended — `--test-all` flag + guard list update (was missing in `--base-dir` guard) |
| `odoo_env/test_helpers.py` | extended — `"test_all": False` default in MockArgs |
| `odoo_env/test_qa.py` | extended — 4 new tests (CLITests + OeIntegrationTests) |

**Evidence**: 46 QA OK, suite 191 OK, `pre-commit` green.

**Fresh review** (run ad7209f8): 1 blocker fixed:
- Blocker: `oe --base-dir /path --test-all` silently exited → added `test_all` to the guard list in `oe.py`.
- Made OeIntegrationTests machine-independent (mock `config.OeConfig` + `Client` instead of `odooenv.OeConfig`).

**Deviation**: `TestAllCommand.execute()` does not signal test failures via exit code (consistent with existing `-Q` behavior; exit code is handled by `python -m odoo_env.qa`).

## PR4 — CI template + docs — pending (phases 8–9)
