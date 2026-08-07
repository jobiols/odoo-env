# Design: qa-coverage-ci

**Change**: `qa-coverage-ci`
**Phase**: Design (ADRs + technical approach)
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-14

## Overview

This change extracts the "run all module tests with coverage" logic (today a hardcoded
reference script, `run_tests.py`) into a reusable engine `odoo_env/qa/`, exposes it via a
CLI, wires it into `oe`, and ships a CI template for client repos. The engine reuses the
existing layered building blocks (`DockerClient`/`RunSpec`, `Client`/`OeConfig`,
`Command`) instead of duplicating docker-command assembly.

The design favors composition over a monolith: a `RunnerConfig` dataclass is the seam, a
`TestRunner` orchestrates discovery → per-module coverage runs → failure detection →
report → threshold, and the CI workflow calls the same CLI that `oe` calls.

```
RunnerConfig (seam)
   ├─ oe builds it from Client/OeConfig         ┐
   └─ qa CLI builds it the same way (CI)         ┘  → same code path

TestRunner(config):
   discover_test_modules() → run_all() → generate_report() → check_threshold()
```

Eight architecture decision records follow, each mapped to the requirements it satisfies.

---

## ADR 1: Package layout and the `RunnerConfig` seam

**Decision**: New subpackage `odoo_env/qa/` with:
- `config.py` → `RunnerConfig` dataclass (the seam),
- `runner.py` → `TestRunner`,
- `failures.py` → ANSI strip + FAIL/ERROR matcher,
- `threshold.py` → read/ratchet the floor,
- `__main__.py` → CLI.

`RunnerConfig` is built by a single factory (`RunnerConfig.from_oe(client, debug=...)`)
that reads `Client`/`OeConfig` exactly as `oe` does. Both `oe --test-all` and the CLI use
that factory, so there is **one** resolution path.

**Rationale**: Matches REQ-QA-007 (auto-resolution). Keeps the engine environment-agnostic
and unit-testable by injecting a plain dataclass rather than reaching into globals.

**Satisfies**: REQ-QA-007, REQ-QA-010.

---

## ADR 2: Reuse `DockerClient`/`RunSpec`, extend for coverage wrapping

**Decision**: Build per-module commands through `DockerClient.get_run_command(RunSpec(...))`.
For the coverage path, set `RunSpec.entrypoint="bash"` and `RunSpec.cmd=["-c", inner]`,
where `inner` is `mkdir -p <covdir> && coverage run -p --source=<addons> "$(command -v odoo)"
-c <conf> <db_args> --stop-after-init --log-level=test --test-enable -i <module>`. Add
`COVERAGE_FILE` via `RunSpec.env`. The DB connection args (`--db_host/port/user/password`)
are passed explicitly because the coverage wrapper bypasses the image entrypoint.

`RunSpec` already has `entrypoint`, `cmd`, and `env`. If a gap appears (e.g. an
ordering issue between `extra_args` and `cmd`), it is fixed minimally in `docker_client.py`
without changing existing call sites.

**Rationale**: The reference script proved this exact mechanism. Reusing the builder avoids
a second docker-command assembler. Writing coverage data under the mounted `data_dir`
(`IN_DATA`, uid 1100 writable) is required because `--rm` discards the container FS.

**Satisfies**: REQ-QA-002.

**Volumes**: reuse `_get_normal_mountings()` (config/data_dir/log/sources/backup_dir) plus
debug mounts when applicable. Coverage data dir = `<IN_DATA>/.coverage_data`.

---

## ADR 3: Discovery — `tests/`-based, distinct from create-test-db

**Decision**: `discover_test_modules()` returns immediate CWD subdirs that have **both**
`__manifest__.py` and a `tests/` folder. This differs intentionally from
`EnvironmentManager.discover_modules_in_cwd()` (which is `__manifest__.py`-only, used to
*install* all modules).

**Rationale**: Only modules with `tests/` have tests to run (REQ-QA-001). Coverage of
modules *without* tests is still counted in the global denominator (REQ-QA-005) because the
`--source` covers the whole addons path, not just tested modules.

**Satisfies**: REQ-QA-001, REQ-QA-005.

---

## ADR 4: Failure detection — exit code OR FAIL/ERROR line

**Decision**: Port `run_tests.py`'s detection verbatim into `failures.py`:
- `ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|[\x07\x08\x0d]")`
- `ERROR_PATTERN = re.compile(r":\s+(FAIL|ERROR): \w")`
Stream each module's output; a run fails if the exit code is non-zero **or** any line
matches `ERROR_PATTERN` after ANSI stripping. Stop at the first failed module, name it,
exit non-zero.

**Rationale**: Odoo can exit 0 on test failure; the gate must not trust the exit code alone
(REQ-QA-003). This is the single most important reliability decision for the CI gate.

**Satisfies**: REQ-QA-003.

---

## ADR 5: Reporting and omit

**Decision**: After all modules pass, run `coverage combine` then `coverage report -m`,
`coverage xml`, `coverage json`, `coverage html` inside a container with the same
`COVERAGE_FILE` env and `--entrypoint bash`. Apply `omit` from `RunnerConfig.omit`
(default: `*/tests/*`, `*/__manifest__.py`, `*/test_*.py`, `*/run_tests.py`). Omit affects
reporting only, never measurement.

**Rationale**: Mirrors the proven reference flow; JSON is added specifically to extract the
total percent for the badge (Ned Batchelder's documented approach).

**Satisfies**: REQ-QA-004.

---

## ADR 6: Threshold storage, enforcement, and ratchet

**Decision**:
- **Storage**: a single repo-versioned file `.coverage-threshold` in the client repo
  containing an integer (default `20`). Easy to edit, easy to diff. (Alternative considered:
  a `[tool.coverage]`/`pyproject` key — rejected for the template because client repos are
  module repos that may not have a `pyproject.toml`.)
- **Enforcement**: `coverage report --fail-under=$(cat .coverage-threshold)`; exit 2 → step
  fails → PR blocked (REQ-QA-005).
- **Ratchet** (REQ-QA-006): a CI guard compares the PR's `.coverage-threshold` against the
  value on `master` (via `git show origin/master:.coverage-threshold`). If the PR value is
  **lower**, the guard fails. Raising is always allowed.
- **Optional auto-raise** (opt-in, master only): if measured coverage exceeds the stored
  floor by a margin, the master job may bump `.coverage-threshold` up and commit it. Default
  OFF to avoid surprises.

**Rationale**: "Adjustable but can only go up" maps cleanly to a versioned integer + a
diff-against-master guard. Keeping auto-raise opt-in respects the human-control principle.

**Satisfies**: REQ-QA-005, REQ-QA-006.

---

## ADR 7: CI test database — thin seed + cache + postgres provisioning

**Decision**:
- **Postgres**: the workflow brings up `pg-<client>` on `odoo-net` from the postgres image
  (a small compose/`docker run` step in the template). The self-hosted runner provides
  Docker and the network; the job ensures the container/network exist idempotently
  (reusing the `docker network create` idempotency already in `DockerClient`).
- **Thin seed**: `odoo -d <client>_test -i base --stop-after-init` (+ `--with-demo` only for
  Odoo ≥19). Demo is default-on for ≤18, giving `admin/admin`. No committed `test.zip`.
- **Cache**: `actions/cache` keyed on the Odoo **image tag** (seed rarely changes). Cache
  payload = an Odoo backup zip / `pg_dump` of `<client>_test`. Miss → build + save; hit →
  restore (REQ-QA-008).
- **Test loop**: per discovered module, `coverage run ... odoo -i <module> --test-enable`
  against the seeded DB.

**Rationale**: Thin seed maximizes cache hits and removes stale-module risk; installing all
modules during the loop is inherent to "always run all modules". The cache key on image tag
(not manifest hash) keeps the seed stable across normal PRs.

**Satisfies**: REQ-QA-008.

**Open detail for apply**: exact seed serialization (oe `--restore`/backup vs raw `pg_dump`).
Prefer reusing `oe` backup/restore plumbing if it works headless on the runner; otherwise
`pg_dump`/`pg_restore` via `docker exec pg-<client>`.

---

## ADR 8: Badge and workflow triggers

**Decision**: One workflow `tests.yml` in the template with two triggers:
- `on: pull_request` → provision + run engine + threshold gate + ratchet guard. **No badge.**
- `on: push: branches: [master]` → same run + `genbadge` `coverage.xml → coverage.svg`,
  committed to the repo; README references the local SVG.
`runs-on: [self-hosted]` (labels parametrized in the template). `htmlcov` uploaded as an
artifact in both cases.

**Rationale**: Badge reflects `master` only (REQ-QA-009). `genbadge` is actively maintained
(`coverage-badge` is in maintenance) and produces a local SVG with no external service —
fully self-contained.

**Satisfies**: REQ-QA-009.

---

## Testing strategy (strict TDD)

Unit tests in `odoo_env/test_qa.py` (unittest, per `openspec/config.yaml`):
- `failures.py`: ANSI strip + pattern matching (FAIL/ERROR/clean) — pure, fast.
- `RunnerConfig.from_oe`: resolution from a mocked `Client`/`OeConfig`.
- `TestRunner.run_all`: command composition (coverage wrapper present/absent, COVERAGE_FILE,
  test-enable) and first-failure stop — mock the docker execution.
- `threshold.py`: read default, enforce, ratchet accept/reject.

The CI template and badge are validated end-to-end on **dimec 17.0e** (manual e2e), since
they cannot run inside odoo-env's pure-python unittest suite.

**Strict TDD note**: RED → GREEN → TRIANGULATE → REFACTOR for every engine unit, using
`PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'`.

---

## Files (engine repo)

| File | Change |
|------|--------|
| `odoo_env/qa/__init__.py` | new |
| `odoo_env/qa/config.py` | `RunnerConfig` + `from_oe` |
| `odoo_env/qa/failures.py` | ANSI strip + matcher |
| `odoo_env/qa/threshold.py` | read/enforce/ratchet |
| `odoo_env/qa/runner.py` | `TestRunner` |
| `odoo_env/qa/__main__.py` | CLI |
| `odoo_env/services/docker_client.py` | minimal extension if needed |
| `odoo_env/oe.py` | `--test-all` flag |
| `odoo_env/odooenv.py` | dispatch to `TestRunner` |
| `odoo_env/test_qa.py` | unit tests |
| `templates/ci/tests.yml` | client workflow template |
| `templates/ci/.coverage-threshold` | default floor (20) |
| `templates/ci/README-badge.md` | badge snippet |
| `README.md` / `docs/` | adoption docs |
