# Tasks: qa-coverage-ci

**Change**: `qa-coverage-ci`
**Phase**: SDD tasks (breakdown for apply)
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-14

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~900–1100 (engine + tests + template + docs) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Delivery strategy | chained |
| Chain strategy | auto-forecast → 4 PRs |

### Suggested chained-PR split

| PR | Scope | Est. lines | Depends on |
|----|-------|-----------|-----------|
| **PR1** | `failures.py` + `RunnerConfig` + `threshold.py` + their unit tests | ~250 | — |
| **PR2** | `TestRunner` (run_all/report/check_threshold) + `DockerClient` extension + tests | ~300 | PR1 |
| **PR3** | `__main__.py` CLI + `oe --test-all` wiring (`oe.py`/`odooenv.py`) + tests | ~200 | PR2 |
| **PR4** | CI template (`templates/ci/`) + docs/README adoption | ~250 | PR3 |

Decision needed before apply: **Yes** (confirm chained split + branch base).
Chained PRs recommended: **Yes**
Chain strategy: chained (4 PRs)
400-line budget risk: **High**

---

## Phase 1 — Infrastructure (test scaffolding)

### 1.1 Scaffold qa subpackage and test module

- [x] 1.1.1 Create `odoo_env/qa/__init__.py` (empty package marker)
- [x] 1.1.2 Create `odoo_env/test_qa.py` with a `QaTestCase(unittest.TestCase)` base and imports
- [x] 1.1.3 Run `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest odoo_env.test_qa` — expect "no tests" (package + module import OK)
- **REQ coverage**: N/A (infrastructure)

---

## Phase 2 — RED/GREEN: failure detection (`failures.py`)

### 2.1 FAIL/ERROR detection

- [x] 2.1.1 RED: `test_detects_fail_line` — `is_error_line(": FAIL: TestFoo")` → True
- [x] 2.1.2 RED: `test_detects_error_line` — `is_error_line(": ERROR: TestBar")` → True
- [x] 2.1.3 RED: `test_ignores_non_test_colon_lines` — `"bad query:"` / `"unique constraint"` → False
- [x] 2.1.4 RED: `test_strips_ansi_before_match` — line with ANSI escapes around `: FAIL: X` → True
- [x] 2.1.5 RED: `test_clean_line_is_false` — normal log line → False
- [x] 2.1.6 Run — expect FAIL (no `failures.py`)
- [x] 2.1.7 GREEN: implement `odoo_env/qa/failures.py` (`ANSI_ESCAPE`, `ERROR_PATTERN`, `is_error_line`)
- [x] 2.1.8 Run — expect PASS
- **REQ coverage**: REQ-QA-003
- **Design reference**: ADR 4

---

## Phase 3 — RED/GREEN: `RunnerConfig` (`config.py`)

### 3.1 RunnerConfig dataclass + from_oe factory

- [x] 3.1.1 RED: `test_runner_config_defaults` — omit defaults, db_name=`<client>_test`, network=`odoo-net`, coverage True
- [x] 3.1.2 RED: `test_from_oe_resolves_fields` — given a mocked `Client` (name/version/base_dir/image), `from_oe` populates client/version/base_dir/image/db_name
- [x] 3.1.3 RED: `test_with_demo_default_by_version` — `with_demo=None` → on for ver ≤18, requires flag for ≥19 (resolved value)
- [x] 3.1.4 Run — expect FAIL
- [x] 3.1.5 GREEN: implement `odoo_env/qa/config.py`
- [x] 3.1.6 Run — expect PASS
- **REQ coverage**: REQ-QA-007, REQ-QA-008 (with_demo)
- **Design reference**: ADR 1, ADR 7

---

## Phase 4 — RED/GREEN: threshold + ratchet (`threshold.py`)

### 4.1 Read + enforce + ratchet

- [x] 4.1.1 RED: `test_read_floor_default_20` — missing `.coverage-threshold` → default 20
- [x] 4.1.2 RED: `test_read_floor_from_file` — file with `35` → 35
- [x] 4.1.3 RED: `test_ratchet_rejects_lower` — master=30, pr=25 → guard fails
- [x] 4.1.4 RED: `test_ratchet_accepts_higher` — master=30, pr=40 → guard passes
- [x] 4.1.5 RED: `test_ratchet_accepts_equal` — master=30, pr=30 → guard passes
- [x] 4.1.6 Run — expect FAIL
- [x] 4.1.7 GREEN: implement `odoo_env/qa/threshold.py` (read_floor, check_ratchet)
- [x] 4.1.8 Run — expect PASS
- **REQ coverage**: REQ-QA-005 (floor), REQ-QA-006 (ratchet)
- **Design reference**: ADR 6

---

## Phase 5 — RED/GREEN: `TestRunner` discovery + command composition

### 5.1 discover_test_modules

- [x] 5.1.1 RED: `test_discover_requires_manifest_and_tests` — `mod_a`(manifest+tests), `mod_b`(manifest+tests), `mod_c`(manifest only) → `["mod_a","mod_b"]`
- [x] 5.1.2 RED: `test_discover_no_modules_returns_empty` — none with tests/ → `[]`
- [x] 5.1.3 RED: `test_discover_does_not_recurse`
- [x] 5.1.4 Run — expect FAIL; GREEN implement; Run — expect PASS
- **REQ coverage**: REQ-QA-001
- **Design reference**: ADR 3

### 5.2 Per-module coverage command composition

- [x] 5.2.1 RED: `test_module_cmd_wraps_with_coverage` — coverage on → command contains `coverage run -p --source=`, `--entrypoint`, `bash`, `-c`, and `COVERAGE_FILE` env under data dir
- [x] 5.2.2 RED: `test_module_cmd_has_test_enable_and_stop_after_init`
- [x] 5.2.3 RED: `test_module_cmd_passes_explicit_db_args` — `--db_host/port/user/password` present
- [x] 5.2.4 RED: `test_module_cmd_no_coverage_when_disabled` — coverage off → no `coverage run` wrapper
- [x] 5.2.5 RED: `test_module_cmd_uses_install_verb` — uses `-i <module>` (thin-seed loop)
- [x] 5.2.6 Run — expect FAIL; GREEN implement (extend `DockerClient`/`RunSpec` minimally if needed); Run — expect PASS
- **REQ coverage**: REQ-QA-002, REQ-QA-008
- **Design reference**: ADR 2, ADR 7

---

## Phase 6 — RED/GREEN: `run_all` orchestration + reporting

### 6.1 First-failure stop

- [x] 6.1.1 RED: `test_run_all_stops_on_fail_line` — mock execution: module 1 streams `: FAIL:` with exit 0 → run_all returns non-zero/raises, names module 1, module 2 NOT run
- [x] 6.1.2 RED: `test_run_all_stops_on_nonzero_exit` — module 1 exit 1, no FAIL line → stop
- [x] 6.1.3 RED: `test_run_all_all_pass_runs_report` — all clean → report generation invoked
- [x] 6.1.4 Run — expect FAIL; GREEN implement; Run — expect PASS
- **REQ coverage**: REQ-QA-003
- **Design reference**: ADR 4

### 6.2 Report generation + omit

- [x] 6.2.1 RED: `test_report_runs_combine_then_reports` — combine before report; xml+json+html produced
- [x] 6.2.2 RED: `test_report_applies_omit_patterns` — omit list present in report command
- [x] 6.2.3 Run — expect FAIL; GREEN implement; Run — expect PASS
- **REQ coverage**: REQ-QA-004
- **Design reference**: ADR 5

### 6.3 Threshold enforcement integration

- [x] 6.3.1 RED: `test_check_threshold_uses_fail_under` — report command includes `--fail-under=<floor>`
- [x] 6.3.2 RED: `test_check_threshold_below_exits_nonzero`
- [x] 6.3.3 Run — expect FAIL; GREEN implement; Run — expect PASS
- **REQ coverage**: REQ-QA-005
- **Design reference**: ADR 5, ADR 6

---

## Phase 7 — RED/GREEN: CLI + `oe` integration

### 7.1 CLI entrypoint

- [x] 7.1.1 RED: `test_cli_builds_config_from_oe` — `python -m odoo_env.qa` path builds `RunnerConfig.from_oe` without explicit client/version
- [x] 7.1.2 RED: `test_cli_exit_nonzero_on_failure` — runner failure → CLI exit != 0
- [x] 7.1.3 Run — expect FAIL; GREEN implement `odoo_env/qa/__main__.py`; Run — expect PASS
- **REQ coverage**: REQ-QA-007
- **Design reference**: ADR 1

### 7.2 oe --test-all flag (without breaking -Q)

- [x] 7.2.1 RED: `test_oe_test_all_dispatches_to_runner` — new flag in `oe.py`, dispatched in `odooenv.build_commands()` → delegates to `TestRunner`
- [x] 7.2.2 RED: `test_oe_dash_q_unchanged` — `-Q sale,stock` still uses existing `qa()` single-run path
- [x] 7.2.3 Run — expect FAIL; GREEN implement; Run — expect PASS
- **REQ coverage**: REQ-QA-010
- **Design reference**: ADR 1

---

## Phase 8 — CI template (client repo artifacts; not unit-tested in odoo-env)

### 8.1 Workflow + threshold + badge template

- [x] 8.1.1 Create `templates/ci/tests.yml` — triggers `pull_request` (gate + ratchet guard) and `push: [master]` (badge); `runs-on: [self-hosted]`; steps: checkout → ensure `odoo-net` + `pg-<client>` → `actions/cache` seed (key=image tag) → provision thin seed (miss) / restore (hit) → `python -m odoo_env.qa` → upload `htmlcov` → (master) `genbadge` `coverage.svg` + commit
- [x] 8.1.2 Create `templates/ci/.coverage-threshold` with `20`
- [x] 8.1.3 Create `templates/ci/README-badge.md` snippet referencing `coverage.svg`
- [x] 8.1.4 Validate workflow YAML syntax (lint/parse)
- **REQ coverage**: REQ-QA-008, REQ-QA-009, REQ-QA-006 (ratchet guard step)
- **Design reference**: ADR 6, ADR 7, ADR 8

---

## Phase 9 — Docs + full verification

### 9.1 Documentation

- [x] 9.1.1 Document the engine + CLI in `README.md` / `docs/` (how `oe --test-all` works)
- [x] 9.1.2 Document client-repo adoption of the CI template (copy `templates/ci/*`, set labels, threshold)

### 9.2 Verification

- [x] 9.2.1 Run full suite: `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'` — all green
- [x] 9.2.2 `pre-commit run -a` clean (black/pylint/type-checker)
- [x] 9.2.3 Manual e2e on **dimec 17.0e**: PR gate fails on a broken test; coverage gate fails below floor; badge updates on master
- **REQ coverage**: all
