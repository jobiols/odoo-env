# qa-coverage Specification

## Purpose

Defines the behavior of the `odoo_env/qa` engine and its CLI, which run the tests
of **all** Odoo modules in a repository with coverage measurement, enforce a global
coverage threshold, and support a CI/CD template for client repositories. The engine
is invokable both by `oe` and directly by GitHub Actions on a self-hosted runner.

## Requirements

### Requirement: REQ-QA-001 — Module test discovery (all modules with tests/)

The engine MUST discover modules to test by scanning the current working directory's
**immediate** subdirectories. A subdirectory MUST be treated as a testable module when
it contains both an `__manifest__.py` file and a `tests/` subdirectory. The engine MUST
collect **all** such modules and MUST NOT scan beyond the immediate children.

#### Scenario: Discovers all modules that have a tests/ folder

- GIVEN the CWD contains `mod_a/` (with `__manifest__.py` and `tests/`),
  `mod_b/` (with `__manifest__.py` and `tests/`), and `mod_c/` (with
  `__manifest__.py` but no `tests/`)
- WHEN test discovery runs
- THEN the collected list MUST be `["mod_a", "mod_b"]`

#### Scenario: No testable modules aborts with a clear message

- GIVEN the CWD contains no subdirectory with a `tests/` folder
- WHEN test discovery runs
- THEN the engine MUST exit non-zero with a message stating no testable modules were found

---

### Requirement: REQ-QA-002 — Coverage-wrapped per-module test run

When coverage is enabled, the engine MUST run each module's tests in its own container,
wrapping Odoo with `coverage run -p --source=<addons>`. Coverage data MUST be written to
a path under the mounted, container-writable data directory (so it survives `--rm`). The
engine MUST override the image entrypoint and pass the database connection parameters
explicitly (host, port, user, password) because the coverage wrapper bypasses the normal
entrypoint. Each per-module run MUST use `--stop-after-init --log-level=test --test-enable`.

#### Scenario: Each module runs under coverage, writing to the data volume

- GIVEN coverage is enabled and modules `["mod_a", "mod_b"]` were discovered
- WHEN `run_all()` executes
- THEN exactly one container MUST run per module
- AND each container's command MUST invoke `coverage run -p --source=<addons>` wrapping odoo
- AND `COVERAGE_FILE` MUST point under the mounted data directory
- AND each run MUST include `--test-enable --stop-after-init`

#### Scenario: Coverage can be disabled (plain test run)

- GIVEN coverage is disabled in the configuration
- WHEN `run_all()` executes
- THEN per-module containers MUST run odoo tests WITHOUT the `coverage run` wrapper

---

### Requirement: REQ-QA-003 — Reliable failure detection

The engine MUST treat a module run as failed when **either** the container exit code is
non-zero **or** the streamed output contains a line matching the Odoo test-failure pattern
`:\s+(FAIL|ERROR): \w` (after stripping ANSI escapes). On the first failed module, the
engine MUST stop, report which module failed, and exit non-zero. The engine MUST NOT rely
on the exit code alone, because Odoo can return exit 0 while a test fails.

#### Scenario: A FAIL line fails the run even with exit code 0

- GIVEN a module run streams a line `... : FAIL: TestFoo.test_bar`
- AND the container exits with code 0
- WHEN failure detection evaluates the run
- THEN the run MUST be considered failed
- AND the engine MUST stop and exit non-zero, naming the failing module

#### Scenario: A non-zero exit fails the run even with no FAIL line

- GIVEN a module run produces no FAIL/ERROR line
- AND the container exits with code 1
- WHEN failure detection evaluates the run
- THEN the run MUST be considered failed

#### Scenario: A clean run passes

- GIVEN a module run has exit code 0 and no FAIL/ERROR line
- THEN the run MUST be considered passed and the engine MUST continue to the next module

---

### Requirement: REQ-QA-004 — Coverage combine and reporting

After all modules pass, the engine MUST combine the parallel coverage data and produce
text, XML, and JSON reports, and an HTML report. Reports MUST apply the configured `omit`
patterns (defaulting to `*/tests/*`, `*/__manifest__.py`, `*/test_*.py`, and the runner
script itself). The omit patterns MUST affect only reporting, not measurement.

#### Scenario: Reports are generated with omit patterns

- GIVEN all modules passed and coverage data exists
- WHEN report generation runs
- THEN `coverage combine` MUST run before reporting
- AND XML, JSON, and HTML reports MUST be produced
- AND the configured omit patterns MUST be applied to every report

---

### Requirement: REQ-QA-005 — Global coverage threshold enforcement

The engine MUST enforce a single **global** coverage percentage over all production code,
where modules without tests count toward the denominator (only tests/manifests/scripts are
omitted). Enforcement MUST use `coverage report --fail-under=<floor>`; when the global
percentage is below the floor, the engine MUST exit non-zero so the PR is blocked. The
floor MUST be read from a repo-versioned, easily editable location (default value: **20**).

#### Scenario: Coverage below the floor fails the gate

- GIVEN the configured floor is `20`
- AND measured global coverage is `18`
- WHEN the threshold check runs
- THEN the engine MUST exit non-zero

#### Scenario: Coverage at or above the floor passes the gate

- GIVEN the configured floor is `20`
- AND measured global coverage is `20`
- WHEN the threshold check runs
- THEN the engine MUST exit zero

#### Scenario: Untested modules lower the global percentage

- GIVEN a module with production code and no tests exists in the repo
- WHEN the global coverage is computed
- THEN that module's uncovered statements MUST be counted in the denominator

---

### Requirement: REQ-QA-006 — Coverage threshold ratchet (never lowers)

The stored coverage floor MUST behave as a ratchet. A change that **lowers** the stored
floor MUST fail the gate. Raising the floor MUST always be allowed. The ratchet check MUST
be deterministic and run in CI on Pull Requests.

#### Scenario: Lowering the floor is rejected

- GIVEN the floor on `master` is `30`
- AND a PR sets the floor to `25`
- WHEN the ratchet guard runs
- THEN the guard MUST fail the PR

#### Scenario: Raising the floor is accepted

- GIVEN the floor on `master` is `30`
- AND a PR sets the floor to `40`
- WHEN the ratchet guard runs
- THEN the guard MUST pass

---

### Requirement: REQ-QA-007 — CLI entrypoint and config resolution

The engine MUST expose a CLI runnable as `python -m odoo_env.qa`. The CLI MUST build a
`RunnerConfig` by auto-detecting `client`, `version`, `base_dir`, and the Odoo `image`
from the oe manifest/config of the checked-out repo, the same way `oe` resolves them.
The CLI exit code MUST be non-zero when any module fails or when coverage is below the floor.

#### Scenario: CLI auto-resolves config and propagates failure

- GIVEN a checked-out client repo with a valid oe manifest
- WHEN `python -m odoo_env.qa` runs and a module test fails
- THEN the config MUST be resolved without explicit client/version arguments
- AND the CLI MUST exit non-zero

---

### Requirement: REQ-QA-008 — Thin-seed test database provisioning (CI)

The CI template MUST provision the test database as a **thin seed** generated by Odoo:
a database initialized with `base` and demo data (demo default-on for Odoo ≤18; `--with-demo`
for ≥19). The seed MUST be cached via `actions/cache` keyed on the Odoo image tag. On a cache
miss the seed MUST be created and saved; on a hit it MUST be restored. The test loop MUST then
install each discovered module with `-i` on that database. No committed `test.zip` may be required.

#### Scenario: Cache miss builds and saves the seed

- GIVEN no cached seed exists for the current Odoo image tag
- WHEN the provisioning step runs
- THEN Odoo MUST initialize `<client>_test` with `base` + demo
- AND the seed MUST be saved to the cache

#### Scenario: Cache hit restores the seed

- GIVEN a cached seed exists for the current Odoo image tag
- WHEN the provisioning step runs
- THEN the seed MUST be restored without re-initializing from scratch

---

### Requirement: REQ-QA-009 — Coverage badge on the main branch

On push to `master`, the CI template MUST regenerate a self-contained coverage badge
`coverage.svg` from the coverage report using `genbadge`, and commit it to the repo. On
Pull Requests, the badge MUST NOT be updated. The client `README.md` MUST reference the
committed `coverage.svg`.

#### Scenario: Badge updates only on master

- GIVEN a push to `master` with a successful coverage run
- WHEN the badge step runs
- THEN `coverage.svg` MUST be regenerated and committed

#### Scenario: PRs do not update the badge

- GIVEN a Pull Request build
- WHEN the workflow runs
- THEN no badge commit MUST be produced

---

### Requirement: REQ-QA-010 — oe integration without breaking -Q

`oe` MUST expose a flag that runs the full "all modules + coverage" engine (e.g.
`oe --test-all`), delegating to the same `TestRunner` used by the CLI. The existing
`oe -Q <modules>` selective-test behavior MUST remain unchanged.

#### Scenario: oe runs the full engine via the new flag

- GIVEN the active client is resolved
- WHEN the new `oe` flag is invoked
- THEN `oe` MUST delegate to `TestRunner` with an auto-built `RunnerConfig`

#### Scenario: oe -Q is unchanged

- GIVEN `oe -Q sale,stock` is invoked
- THEN the existing selective single-run test behavior MUST be used, not the new engine
