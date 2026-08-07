# create-test-db Specification

## Purpose

Defines the behavior of the `oe --create-test-db` command, which creates a
throwaway test database for the active client by restoring an empty seed
database and installing all custom modules found in the client's own
modules repository (`sources_dir/<client>/` — as opposed to `cl-<client>/`,
which holds the extended-manifest/environment module, or any other
dependency repo under `sources_dir/`). The command can be invoked from any
directory; it never depends on the process's current working directory. No
tests are executed.

## Requirements

### Requirement: REQ-CTDB-001 — Command trigger and database naming

The system MUST activate the `--create-test-db` command when `oe` is invoked
with the `--create-test-db` flag. The command MUST resolve the active client
name from `~/.config/oe/oe_config.yaml` and MUST target the database named
`{client}_test` for all subsequent operations (restore and install).

#### Scenario: Trigger resolves client and names the target database

- GIVEN the active client is `dimec` in `~/.config/oe/oe_config.yaml`
- WHEN `oe --create-test-db` is invoked
- THEN the resolved client name MUST be `dimec`
- AND the target database MUST be `dimec_test`

---

### Requirement: REQ-CTDB-002 — Module discovery (client's modules repo, all modules)

The system MUST discover Odoo modules by scanning the **immediate**
subdirectories of the client's own modules repository, `Client.custom_modules_dir`
(`sources_dir/<client>/` — the repo cloned under the bare client name, as
distinct from `cl-<client>/`). This directory is derived from the active
client, never from the process's current working directory, so the command
gives the same result regardless of where it is invoked from. Every
immediate subdirectory that contains an `__manifest__.py` file MUST be
treated as a module. The system MUST collect **all** such modules without
filtering by `tests/` folders or any other criterion. The system MUST NOT
scan beyond the immediate children of `custom_modules_dir`.

#### Scenario: Discovers all module directories in the client's modules repo

- GIVEN `custom_modules_dir` contains subdirectories `module_a/`, `module_b/`,
  and `not_a_module/`
- AND `module_a/__manifest__.py` and `module_b/__manifest__.py` exist
- AND `not_a_module/` does not contain `__manifest__.py`
- WHEN module discovery runs
- THEN the collected module list MUST be `["module_a", "module_b"]`

#### Scenario: Modules with tests/ folders are included

- GIVEN `custom_modules_dir` contains `module_x/` with `__manifest__.py` and
  a `tests/` subdirectory
- WHEN module discovery runs
- THEN `module_x` MUST be in the collected module list

#### Scenario: Nested subdirectories are not scanned

- GIVEN `custom_modules_dir` contains `module_c/` with
  `module_c/__manifest__.py`
- AND `module_c/extra/` also contains `extra/__manifest__.py`
- WHEN module discovery runs
- THEN only `module_c` MUST be in the collected module list
- AND `extra` MUST NOT appear

#### Scenario: Invocation directory never affects discovery

- GIVEN the active client is `dimec`
- AND the process's current working directory is unrelated to `dimec`
  (e.g. `/tmp` or any other repository's checkout)
- WHEN `oe --create-test-db` is invoked
- THEN module discovery MUST scan `dimec`'s `custom_modules_dir`
- AND the result MUST be identical to running the command from inside
  `custom_modules_dir` itself

---

### Requirement: REQ-CTDB-003 — Seed restore via copy-up

The system MUST restore a known empty seed database before installing modules.
The seed archive MUST be located at `backup_dir/bkp_test/test.zip`. Because the
restore container only mounts `backup_dir/`, the system MUST first copy
`backup_dir/bkp_test/test.zip` into `backup_dir/test.zip`, then invoke restore
with the equivalent of `oe --restore -d {client}_test --no-deactivate -f
test.zip`, and finally delete the temporary `backup_dir/test.zip` copy. The
system MUST NOT modify the `BackupManager.restore` contract or signature.

#### Scenario: Seed is copied up, restored, and cleaned up

- GIVEN `backup_dir/bkp_test/test.zip` exists and is a valid seed archive
- WHEN the seed restore step runs
- THEN `backup_dir/test.zip` MUST be created as a copy of
  `backup_dir/bkp_test/test.zip`
- AND a restore MUST be invoked targeting database `{client}_test` with
  `--no-deactivate` and `-f test.zip`
- AND `backup_dir/test.zip` MUST be deleted after the restore completes

#### Scenario: Restore uses the existing BackupManager.restore contract

- GIVEN a `BackupManager` instance
- WHEN the restore is invoked
- THEN the call MUST use the existing `BackupManager.restore(database,
  backup_file, no_deactivate)` signature
- AND no new parameters or overloaded variants MUST be introduced to
  `BackupManager`

---

### Requirement: REQ-CTDB-004 — Module install with -i and no --test-enable

After the seed restore completes, the system MUST install all discovered
modules into the target database. The install MUST reuse the same docker-run
builder pattern used by `EnvironmentManager.update()`, but MUST emit `-i`
(install) instead of `-u` (update). The docker invocation MUST include
`--stop-after-init -d {client}_test`. The system MUST NOT pass
`--test-enable`.

#### Scenario: Install runs with -i on the test database

- GIVEN the discovered modules are `["module_a", "module_b"]`
- AND the target database is `dimec_test`
- WHEN the install step runs
- THEN a docker run command MUST be built using the same volume, network, and
  environment configuration as `EnvironmentManager.update()`
- AND the command MUST include `-i module_a,module_b`
- AND the command MUST include `--stop-after-init -d dimec_test`
- AND the command MUST NOT include `--test-enable`

#### Scenario: Install does not pass --test-enable even if a tests/ folder exists

- GIVEN discovered module `module_x` contains a `tests/` subdirectory
- WHEN the install step runs
- THEN `--test-enable` MUST NOT appear in the docker run command

---

### Requirement: REQ-CTDB-005 — Edge case: no modules found

If module discovery finds **zero** modules (no immediate subdirectory of
`custom_modules_dir` contains `__manifest__.py`), the system MUST abort
with a clear, human-readable error message. The system MUST NOT proceed to the
restore step. The system MUST NOT invoke docker.

#### Scenario: Aborts before restore when custom_modules_dir has no module dirs

- GIVEN `custom_modules_dir` contains no immediate subdirectories with
  `__manifest__.py`
- WHEN `oe --create-test-db` is invoked
- THEN the system MUST emit an error message indicating no modules were found
- AND the system MUST NOT copy or restore any seed database
- AND the system MUST NOT invoke docker

---

### Requirement: REQ-CTDB-006 — Edge case: target database already exists

If the target database `{client}_test` already exists, the system MUST prompt
the user for confirmation before overwriting it (the restore step recreates the
database). The system MUST abort without any changes when the user declines.
The system MUST also abort without changes when running in a non-interactive
context (e.g., piped input, redirected stdin) where a confirmation prompt cannot
be answered.

#### Scenario: User confirms overwrite of existing test database

- GIVEN the database `dimec_test` already exists
- AND the terminal is interactive
- WHEN `oe --create-test-db` is invoked and the user responds affirmatively
- THEN the command MUST proceed with restore and install

#### Scenario: User declines overwrite of existing test database

- GIVEN the database `dimec_test` already exists
- AND the terminal is interactive
- WHEN `oe --create-test-db` is invoked and the user responds negatively
- THEN the system MUST abort with a message indicating the user chose not to
  overwrite
- AND the target database MUST NOT be modified
- AND no restore or install MUST occur

#### Scenario: Non-interactive context aborts on existing database

- GIVEN the database `dimec_test` already exists
- AND stdin is not a terminal (non-interactive context)
- WHEN `oe --create-test-db` is invoked
- THEN the system MUST abort with a message indicating that the database exists
  and interactive confirmation is required
- AND the target database MUST NOT be modified
- AND no restore or install MUST occur

---

### Requirement: REQ-CTDB-007 — Order of operations

The system MUST enforce the following order of operations:

1. Module discovery (REQ-CTDB-002), including the zero-modules guard
   (REQ-CTDB-005).
2. Seed restore (REQ-CTDB-003).
3. Module install (REQ-CTDB-004).

The ordering MUST guarantee that the zero-modules abort happens **before** any
destructive step (restore or install), and that the seed restore completes
**before** module installation begins.

#### Scenario: No modules aborts before restore

- GIVEN `custom_modules_dir` contains no modules
- WHEN `oe --create-test-db` is invoked
- THEN the abort for "no modules found" MUST be raised before any file copy,
  restore, or docker invocation

#### Scenario: Restore completes before install

- GIVEN `custom_modules_dir` contains at least one module
- WHEN `oe --create-test-db` is invoked
- THEN the seed restore MUST complete successfully before the docker install
  command is issued

---

## Non-Requirements (explicitly out of scope)

The following behaviors are intentionally NOT specified and MUST NOT be
implemented in this change:

- **No test execution**: the `--test-enable` flag is never passed; no test suite
  is run after install.
- **No tests/-folder filtering**: all modules are installed regardless of
  whether they have a `tests/` directory.
- **No `-m` override**: there is no flag or parameter to specify a directory
  other than the client's `custom_modules_dir` for module discovery.
- **No git-repos derivation**: module discovery does not parse
  `__manifest__.py` `git-repos` keys, nor does it derive modules from the
  project manifest.
- **No dependency repo installation**: localization repos (`sub_*`), the
  `cl-<client>` environment/manifest repo, and any other repo under
  `sources/` besides `custom_modules_dir` (`sources/<client>/`) are never
  installed.
- **No extra base modules**: only the modules discovered in `custom_modules_dir`
  are installed; the system does not add any hardcoded base or core modules
  beyond what Odoo resolves from the module dependency graph.
