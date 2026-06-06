# Explore Report: create-test-db

**Change**: `create-test-db`
**Phase**: Explore
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-06

## 1. Change idea

Implement the `--create-test-db` flag in `oe`. The flag is already declared in
argparse but unimplemented: invoking it only raises an error. The goal is to
port the behavior of the per-project bash script `create_test_db.sh` into `oe`
as a native command.

Functional intent: build a throwaway **test database** for the current project
by (a) restoring a known empty test database and (b) installing all of the
project's own modules into it (no test run).

## 2. Current state (evidence)

| Location | Current behavior |
| --- | --- |
| `odoo_env/oe.py:179` | `--create-test-db` declared, `action="store_true"`, help text "Create database with demo data." (misleading). |
| `odoo_env/oe.py:220` | `args.create_test_db` included in the "is any action requested" guard. |
| `odoo_env/odooenv.py:90-91` | Dispatch point in `build_commands()`: `if self._args.create_test_db: msg.err("create-test-db is not yet implemented.")` |

## 3. Reference bash script (`create_test_db.sh`)

Lives inside client projects (e.g. `sources/dimec/create_test_db.sh`). Three steps:

1. **Discover modules**: scans the CWD subdirectories and builds a comma list of
   modules that contain a `tests/` folder. *(User overrode this: install ALL
   project modules, not only those with `tests/`.)*
2. **Restore empty test DB**:
   ```sh
   cp $BASE/${CLIENT}/backup_dir/bkp_test/test.zip $BASE/${CLIENT}/backup_dir/
   oe --restore -d ${CLIENT}_test --no-deactivate -f test.zip
   rm $BASE/${CLIENT}/backup_dir/test.zip
   ```
   The copy-up exists because the restore container only mounts `backup_dir/`
   as `/backup`; the empty seed lives in the `bkp_test/` subfolder.
3. **Install modules**: `docker run ... --stop-after-init -d ${CLIENT}_test -i $MODULES`
   with volumes (config, data_dir, sources, backup_dir), network `odoo-net`,
   `ODOO_CONF=/dev/null`. `--test-enable` is commented out → install only.

## 4. Settled user decisions (do not re-litigate)

1. Install **ALL** modules in the project's module repo (dirs with `__manifest__.py`), not only those with `tests/`.
2. Empty test DB comes from the fixed convention `backup_dir/bkp_test/test.zip`.
3. Target DB name is fixed: `{client}_test`.
4. Do **not** pass `--test-enable` (install only, no test run).
5. Full SDD lifecycle, interactive mode.

## 5. Reuse surface (existing building blocks)

| Need | Existing code | Notes |
| --- | --- | --- |
| Restore DB | `OdooEnv.restore()` → `BackupManager.restore(database, backup_file, no_deactivate)` (`managers/backup_manager.py`) | Uses `DBTOOLS_IMAGE`, mounts `backup_dir → /backup`. To restore from `bkp_test/test.zip` we must either copy the seed up to `backup_dir/` (script approach) or extend the mount/`ZIPFILE` to reach the subdir. |
| Install modules via docker | `EnvironmentManager.update(database, modules)` (`managers/environment_manager.py:321`) | Builds the EXACT docker run needed (volumes via `_get_normal_mountings`/`_get_debug_mountings`, `network="odoo-net"`, `links={pg-{client}:db}`, `env ODOO_CONF=/dev/null`, `stop_after_init=True`) but emits `-u` (update). A fresh empty DB needs `-i` (install). |
| `{client}_test` naming | `EnvironmentManager.qa()` (`:349`) already uses `{client}_test` | Reuse the convention. |
| Run-command builder | `DockerClient.get_run_command(...)` (`services/docker_client.py:143`) | Has `stop_after_init`, `extra_args`, `test_enable`, etc. The `-u`/`-i` difference is just the `extra_args` verb. |
| Module dir scan | `Client._discover_manifest_from_path()` (static, `client.py`) | Walks a tree for `__manifest__.py`; adaptable, but it returns the FIRST match — module discovery needs ALL immediate module dirs. |
| Filesystem ops | `SystemClient` (`services/system.py`) — `get_rm_command`, `get_chmod_command`, etc. | Available if we replicate the copy-up/cleanup as Command steps. |
| Command pattern | `command.py` | Project rule: prefer extending `Command` subclass over ad-hoc subprocess. |

Implication: the feature is **composition of existing pieces** + a module-discovery
helper + an install (`-i`) variant of the update builder. Low architectural risk.

## 6. CRITICAL open design question — module discovery

**Problem**: identify WHICH directory holds the project's own modules to install.

Findings:
- The module repo is **not** always named like the client (user may work on a
  library repo such as `addons_accounting`).
- The client is always defined in `~/.config/oe/oe_config.yaml` (`client:` key).
- In `oe_config.yaml`, each client maps to a `client_path` pointing to the
  **project manifest dir** (the `cl-<client>/<client>_default` repo holding
  `__manifest__.py` with `git-repos`), e.g.
  `dimec → /odoo/ar/odoo-17.0e/dimec/sources/cl-dimec/dimec_default`.
  This is NOT the modules dir.
- `sources/` contains: the `cl-<client>` definition repo, the project's own
  module repo(s), and `sub_*` localization dependency repos (hundreds of OCA
  modules that MUST NOT be installed).
- For dimec: 14 custom modules live in `sources/dimec/`.
- The bash script sidestepped this by running from the CWD (the module repo dir).

### Candidate strategies (for the proposal to decide)

**Option A — Current working directory (CWD).**
Scan the directory `oe` is invoked from for immediate subdirs with `__manifest__.py`.
- ✅ Mirrors the bash script exactly; works for any repo name including libraries.
- ✅ Zero new config; intuitive ("the project I'm standing in").
- ⚠️ `oe` today is largely path-agnostic; introduces CWD dependency for this command.
- ⚠️ Footgun if run from the wrong dir (e.g. `sources/` root → would scan repo dirs, not modules).

**Option B — Derive from `git-repos` in the project manifest.**
Parse the project manifest (`client_path`'s `__manifest__.py`) `git-repos`; take
entries that clone directly to `sources/<name>` WITHOUT a sub-path, excluding
`cl-*` (definition) and treating `sub_*`-targeted entries as deps.
- ✅ No CWD dependency; fully derived from project metadata.
- ⚠️ Heuristic (naming conventions `cl-*`, sub-path = dependency) may not be universal.
- ⚠️ More complex; couples discovery to repo-URL parsing.

**Option C — Explicit parameter.**
`oe --create-test-db -m <repo_or_path>` (or a `module-repo` arg) to name the dir.
- ✅ Unambiguous; supports the library case explicitly.
- ⚠️ Extra step for the user; the script had zero args.
- Could combine with A as a default + override.

**Recommendation to carry into proposal**: lead with **Option A (CWD) as the
default**, optionally backstopped by **Option C** (explicit override) for edge
cases. Rationale: matches the proven script behavior, handles the
`addons_accounting` library case naturally (you run it from that repo), and
avoids brittle `git-repos` parsing. The proposal question round should confirm
CWD-vs-explicit and define the guardrail (e.g. refuse if no `__manifest__.py`
dirs found, or if CWD looks like `sources/` root).

## 7. Restore copy-up nuance (decide in design)

`BackupManager.restore` mounts only `backup_dir → /backup`. The seed lives at
`backup_dir/bkp_test/test.zip`. Two approaches:
- **A** Replicate the script: copy seed → `backup_dir/`, restore with
  `-f test.zip`, then delete the copy (Command steps via `SystemClient`).
- **B** Extend restore to accept a sub-path / mount `bkp_test/` (cleaner, but
  touches the restore contract).
Lean A for minimal blast radius; revisit in design.

## 8. Affected modules (per project rule)

- `odoo_env/oe.py` (help text only)
- `odoo_env/odooenv.py` (`create_test_db()` method + dispatch)
- `odoo_env/managers/environment_manager.py` (install `-i` variant + module discovery, or a new helper)
- `odoo_env/managers/backup_manager.py` (only if Option B for restore)
- New/updated tests under `odoo_env/test_*.py`

## 9. Risks

- **Module-discovery rule** is the main correctness risk (installing deps by mistake, or missing modules). Must be nailed in proposal/design.
- **Destructive on the DB**: `{client}_test` is dropped/recreated on restore. Acceptable (test DB) but document it.
- **CWD coupling** (if Option A) is a behavior change vs the rest of `oe`.
- `-i` vs `-u`: installing already-installed modules is idempotent-ish in Odoo, but on a truly empty seed `-i` is correct.

## 10. Next phase

Proceed to **proposal** with a product question round focused on:
1. Module discovery: CWD default vs explicit `-m` override vs git-repos derivation; and the guardrail behavior.
2. Restore approach (copy-up vs extended restore).
3. Behavior when the target test DB already exists / when no modules are found.
