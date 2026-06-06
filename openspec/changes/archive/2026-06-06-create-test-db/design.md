# Design: create-test-db

**Change**: `create-test-db`
**Phase**: Design (ADRs + technical approach)
**Artifact store**: OpenSpec
**Strict TDD**: true
**Date**: 2026-06-06

## Overview

The `oe --create-test-db` flag is already declared in argparse (`odoo_env/oe.py:179`) but
unimplemented — `build_commands()` raises `msg.err("create-test-db is not yet implemented.")`
(`odoo_env/odooenv.py:91`).

This design implements the flag by composing existing building blocks (restore, docker-run
builder) with a new module-discovery helper, two guard phases (zero-modules check,
existing-DB confirmation), and file-copy cleanup modeled as Command steps. The result is a
single `OdooEnv.create_test_db()` method dispatched from `build_commands()` that returns a
list of Command objects representing:

```
discovery → guard(zero-modules) → guard(DB-exists confirm) → copy-up → restore → cleanup → install
```

Seven architecture decision records follow, each mapped to the requirements they satisfy.

---

## ADR 1: Where `create_test_db()` lives and how it composes steps

**Decision**: Add a new `OdooEnv.create_test_db()` method dispatched from
`build_commands()`, returning `list[Command]`. The method performs guard checks inline
(before building any Command objects) and then assembles the Command list from existing
managers.

**Rationale**:
- Matches the existing pattern exactly: `restore()`, `update()`, and `qa()` are all
  methods on `OdooEnv` that return `list[Command]`, dispatched by `build_commands()`
  (`odoo_env/odooenv.py:42-92`).
- `oe.py` main flow is `commands = oe.build_commands()` → `oe.execute(commands)` — the
  method must return a list of Command objects for the executor to iterate.
- Guard checks (zero modules, DB exists) must abort BEFORE any Command is built so that
  no destructive command ever reaches the execute queue (see ADR 6).

**Dispatch change** (`odoo_env/odooenv.py:90-91`):
```python
# Before:
if self._args.create_test_db:
    msg.err("create-test-db is not yet implemented.")

# After:
if self._args.create_test_db:
    commands += self.create_test_db()
```

**Composition inside `create_test_db()`** (pseudocode):
1. `modules = EnvironmentManager.discover_modules_in_cwd()` — ADR 2
2. If `len(modules) == 0`: `msg.err("No modules found...")` — REQ-CTDB-005
3. `database = f"{self.client.name}_test"`
4. If `self._db_exists(database)`: confirm or abort — ADR 5
5. Build and return Command list: copy + restore + rm + install — ADRs 3, 4

**Alternatives considered**:
- Placing the logic in `EnvironmentManager` directly: rejected because `build_commands()`
  dispatches from `OdooEnv`, and the method returns commands consumed by
  `OdooEnv.execute()`. A manager method would still need an `OdooEnv` wrapper.
- Building a single "CreateTestDbCommand": rejected because the composition of restore +
  install uses existing manager contracts that return multiple Commands; flattening them
  into one would break the Command granularity used everywhere else.

**Satisfies**: REQ-CTDB-001, REQ-CTDB-007

---

## ADR 2: Module discovery — CWD-only helper, static on EnvironmentManager

**Decision**: Add a `@staticmethod` method `discover_modules_in_cwd()` on
`EnvironmentManager`. It scans `os.getcwd()` for immediate child directories that contain
`__manifest__.py`, and returns a sorted list of directory names.

**Contract**:
```python
@staticmethod
def discover_modules_in_cwd() -> list[str]:
    """
    Scan the current working directory for immediate subdirectories
    containing __manifest__.py. Returns sorted module name list.

    Does NOT recurse into subdirectories.
    Does NOT filter by tests/ folders.
    """
    cwd = Path(os.getcwd())
    modules = []
    for entry in cwd.iterdir():
        if entry.is_dir() and (entry / "__manifest__.py").is_file():
            modules.append(entry.name)
    return sorted(modules)
```

**Rationale**:
- The existing `Client._discover_manifest_from_path()` (`client.py:123-137`) walks
  recursively and returns only the FIRST match — it is designed for finding the project
  manifest, not for enumerating module directories. Reusing it would require rewriting
  its contract, which breaks the single-responsibility principle.
- `EnvironmentManager` is the natural home: it already builds all docker-run commands
  that consume module lists (`update()`, `qa()` — `environment_manager.py:321,349`), so
  module discovery lives alongside module consumption.
- `staticmethod` requires no `self` or `parent` — it only touches the filesystem at
  `os.getcwd()`, making it trivially testable by patching `os.getcwd` + `Path.iterdir`.

**Why not `Client`**: Client is about project manifests, image resolution, and directory
paths (`client.py`). Module discovery in CWD is an environment operation, not a client
configuration operation.

**Why not a separate helper module**: One static method does not justify a new module.

**Edge cases covered**:
- **No subdirectories**: returns empty list (handled by zero-modules guard).
- **File named `__manifest__.py` at CWD root**: `Path.is_dir()` check prevents false
  positives.
- **Symlinks**: `iterdir()` + `is_dir()` follows symlinks; if a symlinked dir contains
  `__manifest__.py`, it is discovered. This is acceptable — if the user put a symlink
  there, they intend it.
- **Hidden directories (`.git`, etc.)**: `iterdir()` includes them, but they won't
  contain `__manifest__.py`. No special filtering needed.

**Satisfies**: REQ-CTDB-002

---

## ADR 3: Install variant — parameterize the docker-run builder with `_build_module_command`

**Decision**: Extract a private `_build_module_command(database, modules, verb)` method
on `EnvironmentManager` that builds the shared docker-run scaffolding, accepting `"-i"`
(install) or `"-u"` (update) as the `verb` parameter. Both `update()` and the new install
step call it.

**Code structure** (`odoo_env/managers/environment_manager.py`):

```python
def _build_module_command(self, database, modules, verb):
    """Build docker run command for -i (install) or -u (update) modules."""
    ret = []
    volumes = self._get_normal_mountings()
    if self.parent.debug:
        volumes.update(self._get_debug_mountings())

    cmd_list = self.docker_client.get_run_command(
        self.parent._client.get_image("odoo").name,
        interactive=True,
        remove=True,
        network="odoo-net",
        volumes=volumes,
        links={f"pg-{self.parent._client.name}": "db"},
        env={"ODOO_CONF": "/dev/null"},
        stop_after_init=True,
        logfile="false",
        extra_args=["-d", database, verb, ", ".join(modules)],
    )

    action = "Installing" if verb == "-i" else "Updating"
    ret.append(
        Command(
            self.parent,
            command=cmd_list,
            usr_msg=f"{action} {', '.join(modules)} on database {database}",
        )
    )
    return ret
```

Then `update()` (`environment_manager.py:321`) becomes:
```python
def update(self, database, modules):
    return self._build_module_command(database, modules, "-u")
```

And the install step in `create_test_db()` calls:
```python
env_mgr = EnvironmentManager(self)
install_commands = env_mgr._build_module_command(database, modules, "-i")
```

**`get_run_command` args are identical** for both verb values:
- `interactive=True, remove=True, network="odoo-net"` — same as update
- `volumes`: same `_get_normal_mountings()` + optional debug mountings — same as update
- `links={f"pg-{client}": "db"}` — same as update
- `env={"ODOO_CONF": "/dev/null"}` — same as update
- `stop_after_init=True, logfile="false"` — same as update
- **`test_enable` is NOT passed** (defaults `False`) — REQ-CTDB-004
- `extra_args=["-d", database, verb, ", ".join(modules)]` — verb is the only difference

**Why not duplicate `update()` with `-i`**: Violates DRY; makes future changes to volumes
or links require edits in two places.

**Why not pass `test_enable` even if `tests/` folders exist**: The spec (REQ-CTDB-004
scenario 2) explicitly forbids it. `test_enable` is only for `qa()`.

**Alternatives considered**:
- Adding a boolean `install` parameter to `update()`: rejected because `update()` is a
  public API consumed by `OdooEnv.update()`, and changing its signature creates
  unnecessary coupling.
- Calling `get_run_command` directly from `create_test_db()`: rejected because it
  duplicates the volume/link/env scaffolding.

**Satisfies**: REQ-CTDB-004

---

## ADR 4: Seed restore copy-up — modeled as Command steps

**Decision**: Model the copy-up as three sequential `Command` objects: host-side `cp`,
`BackupManager.restore()`, and host-side `rm`. All run on the HOST filesystem. The
`BackupManager.restore()` contract is NOT modified.

**Sequence** (inside `create_test_db()`):
```
1. Command(parent, command=["cp", "{backup_dir}/bkp_test/test.zip", "{backup_dir}/test.zip"],
           usr_msg="Copying seed database")
2. BackupManager.restore(database="{client}_test", backup_file="test.zip", no_deactivate=True)
   → returns [Command(...)]
3. Command(parent, command=["rm", "{backup_dir}/test.zip"],
           usr_msg="Removing temporary seed copy")
```

**Why host-side `cp`/`rm` and not Python `shutil`**:
- The project rule mandates extending the `Command` subclass pattern
  (`openspec/config.yaml` design rules).
- SystemClient (`services/system.py`) has no `cp` equivalent. Adding one is unnecessary
  — `cp` and `rm` in a Command list are simple, reviewable, and consistent with how the
  rest of the codebase uses the `Command` class for one-off shell commands.
- The `rm` uses no `sudo` by default (bare `["rm", path]`) because `backup_dir/` is
  user-owned. If needed in the future, a `RemovedirCommand`-like check_args pattern can
  be adopted.

**Source-existence guard**: Before building the copy Command, check:
```python
seed_path = Path(self.client.backup_dir) / "bkp_test" / "test.zip"
if not seed_path.is_file():
    msg.err(f"Seed database not found at {seed_path}. Cannot create test database.")
```
This runs at build time, before any Command is executed.

**Why not extend BackupManager to accept sub-paths**:
- The explore report evaluated this (section 7) and recommended Option A (copy-up) for
  minimal blast radius.
- `BackupManager.restore()` is used by `oe --restore` and has a stable, tested contract
  (`backup_manager.py:11-43`). Changing it to mount subdirectories would risk breaking
  existing restore behavior.
- Once `test.zip` is copied to `backup_dir/`, the restore container sees it at
  `/backup/test.zip` via the existing volume mount `backup_dir → /backup`
  (`backup_manager.py:24`).

**Why `no_deactivate=True`**: The target is a throwaway test DB from a seed — there is
no production database to deactivate. Passing `no_deactivate=True` avoids the
`DEACTIVATE=True` env var in the dbtools container (`backup_manager.py:31`).

**Satisfies**: REQ-CTDB-003

---

## ADR 5: Existing-DB confirmation + non-interactive abort

**Decision**: Implement DB-existence detection as a private `_db_exists(database)` method
on `OdooEnv` that queries the postgres container via `docker exec`. Implement
confirmation as an `input()` prompt guarded by `sys.stdin.isatty()`. Both run during
`build_commands()` before any Command objects are created.

**DB-existence detection**:
```python
def _db_exists(self, database):
    """Check if a database exists in the postgres container.

    Queries pg_database via docker exec on pg-{client}. Requires the
    postgres container to be running (assumed for --create-test-db).
    """
    result = subprocess.run(
        ["docker", "exec", f"pg-{self.client.name}",
         "psql", "-U", "odoo", "-tAc",
         f"SELECT 1 FROM pg_database WHERE datname='{database}'"],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "1"
```

**Why `docker exec psql`**:
- The codebase has no existing DB-detection mechanism. `BackupManager` restores into a
  DB but doesn't check existence — PostgreSQL `CREATE DATABASE` handles conflicts
  server-side.
- The postgres container is named `pg-{client}` (`environment_manager.py:146` —
  `name=f"pg-{self.parent._client.name}"`). It's always on `odoo-net`. A `docker exec`
  query is the simplest way to reach it without adding a psycopg2 dependency.
- The pg container must be running for restore and install anyway — this is an
  acceptable precondition.

**Confirmation prompt**:
```python
import sys

def _confirm_overwrite(self, database):
    """Prompt user to confirm overwriting an existing database.
    Returns True on 'y'/'yes', False on anything else.
    Aborts with msg.err() in non-interactive contexts.
    """
    if not sys.stdin.isatty():
        msg.err(
            f"Database '{database}' already exists and stdin is not a terminal.\n"
            "Cannot prompt for confirmation. Drop the database manually or "
            "run from an interactive terminal."
        )
    try:
        answer = input(
            f"Database '{database}' already exists. Overwrite? [y/N]: "
        ).strip().lower()
    except EOFError:
        msg.err(
            f"Database '{database}' already exists and input stream ended.\n"
            "Cannot prompt for confirmation. Aborting."
        )
    return answer in ("y", "yes")
```

**Why not use the `msg` module for prompting**: `messages.py` (`odoo_env/messages.py`)
has no prompt function — it only has `run`, `done`, `err`, `inf`, `warn`. Adding a
prompt method to `Msg` would couple the messaging layer to `input()`. Keeping the prompt
in `OdooEnv` is simpler and makes it mockable via `builtins.input`.

**Guard placement**: Both `_db_exists` and `_confirm_overwrite` run inside
`create_test_db()`, BEFORE the Command list is built:

```python
def create_test_db(self):
    modules = EnvironmentManager.discover_modules_in_cwd()
    if not modules:
        msg.err("No Odoo modules found in the current directory. ...")
    database = f"{self.client.name}_test"
    if self._db_exists(database):
        if not self._confirm_overwrite(database):
            msg.err("Aborted by user. Test database was not modified.")
    # ... build commands only if guards pass
```

**Satisfies**: REQ-CTDB-006

---

## ADR 6: Ordering and guard enforcement — build-time vs execute-time

**Decision**: The zero-modules guard (REQ-CTDB-005) and existing-DB confirmation
(REQ-CTDB-006) MUST execute at **build time** (inside `create_test_db()`, called from
`build_commands()`), before any Command objects are created. They raise `OeError` via
`msg.err()` to abort, which is caught by `main()` in `oe.py:234` (`except OeError:
sys.exit(1)`).

**Why build-time and not execute-time**:

The `build_commands()` / `execute()` lifecycle is:
```
oe.py:232  oe = OdooEnv(args)
oe.py:233  commands = oe.build_commands()
oe.py:234  oe.execute(commands)
```

If the guards were modeled as `Command.check()` logic:
1. The restore and install Commands would already be in the list — an anti-pattern
   because we built potentially destructive commands that we intend to skip.
2. A Command with a failing `check()` is simply skipped, but the remaining Commands in
   the list continue executing. We'd need a mechanism to abort the entire pipeline.
3. `Command.check()` returns `True`/`False` — it cannot abort the program.

By running guards at build time, we ensure that **zero Command objects exist** when the
guards fail. The `msg.err()` call raises `OeError`, which propagates through
`build_commands()` to `main()`, and the program exits with code 1 before `execute()` is
ever reached.

**Why not use `Command.check()` for the zero-module guard**:
- There is no natural Command to attach it to. We could create a synthetic
  "GuardCommand", but that's indirection for its own sake.
- The guard's purpose is to prevent building commands, not to skip one command in a
  chain.

**Why not defer DB-exists check to restore Command**:
- The restore step recreates the DB unconditionally — `BackupManager.restore()` has no
  existence check. Adding one would change a contract the proposal explicitly leaves
  untouched.
- The user must confirm BEFORE any file copy or docker invocation happens. Build-time
  confirmation ensures this.

**Sequence enforcement (REQ-CTDB-007)**:

The guard-abort-before-building pattern naturally enforces ordering:

```
create_test_db():
    1. modules = discover_modules_in_cwd()     ← discovery (build-time)
    2. if not modules: msg.err(...)             ← zero-module guard (build-time, aborts)
    3. database = resolve_target_db()           ← naming (build-time)
    4. if _db_exists(database):
           if not confirm: msg.err(...)         ← DB-exists guard (build-time, aborts)
    5. commands = []                            ← only reached if guards pass
    6. commands += [copy_cmd]                   ← step 1 of destructive ops
    7. commands += backup_mgr.restore(...)      ← step 2: restore
    8. commands += [rm_cmd]                     ← step 3: cleanup
    9. commands += env_mgr._build_module_command(...)  ← step 4: install
   10. return commands
```

`execute()` then runs `commands[0]` (copy), `commands[1]` (restore), `commands[2]` (rm),
`commands[3]` (install) in order. Each `Command.execute()` is synchronous (blocking
subprocess call), so the sequence is guaranteed.

**Satisfies**: REQ-CTDB-007, REQ-CTDB-005

---

## ADR 7: Dead-code removal — deleting `odoo_env/create_database.py`

**Decision**: Delete `odoo_env/create_database.py` entirely. It has zero callers.

**Evidence**:
- `grep -r "create_database" odoo_env/` returns only the definition inside the file
  itself — no imports, no references from any other Python module.
- `grep -r "from.*create_database\|import.*create_database" odoo_env/` returns zero
  matches.
- The only references outside the file are in PlantUML documentation
  (`packages_odoo_env.plantuml` and `doc/uml/packages_odoo_env.plantuml`) which are
  stale and not executed.
- The file's code is broken: `subprocess.call(command_string)` without `shell=True`
  (line 21) would raise `FileNotFoundError` if ever called.

**Code removed**:
- `restore_database(cli)` — duplicates BackupManager logic with hardcoded image name
  `jobiols/dbtools:1.3.1` (the codebase uses `DBTOOLS_IMAGE` from `constants.py`).
- `create_backup_db(client)` — tells the user to create a DB manually.
- `create_database(_oe, client_name)` — unwired entry point.

**No rollback risk**: If removal ever needs to be undone, the file can be restored from
git history. It has never been wired to any CLI flag or import chain.

**Satisfies**: proposal scope (dead-code removal item)

---

## Component and sequence summary

```
┌─ oe.py main() ────────────────────────────────────────────────────┐
│                                                                    │
│  args.create_test_db == True                                       │
│       │                                                            │
│       ▼                                                            │
│  oe.build_commands()                                               │
│       │                                                            │
│       ▼                                                            │
│  OdooEnv.create_test_db()                                          │
│       │                                                            │
│       ├── 1. modules = EnvironmentManager.discover_modules_in_cwd()
│       │       (scan os.getcwd(), sort names)                       │
│       │                                                            │
│       ├── 2. if not modules: msg.err("No modules...") ───► exit 1 │
│       │                                                            │
│       ├── 3. database = f"{client}_test"                           │
│       │                                                            │
│       ├── 4. if _db_exists(database):                              │
│       │       if not _confirm_overwrite(database):                 │
│       │           msg.err("Aborted...") ──────────► exit 1         │
│       │                                                            │
│       └── 5. Build Command list:                                   │
│               [cp seed → backup_dir/]                              │
│               [BackupManager.restore(...)]                         │
│               [rm backup_dir/test.zip]                             │
│               [EnvironmentManager._build_module_command(...)]      │
│                                                                    │
│  oe.execute(commands)                                              │
│       │                                                            │
│       ├── Command 1: cp → copy seed to backup_dir                  │
│       ├── Command 2: docker run dbtools → restore test.zip         │
│       ├── Command 3: rm → delete temporary copy                    │
│       └── Command 4: docker run odoo → -i modules --stop-after-init│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### File changes

| File | Change | Lines (est.) |
|------|--------|-------------|
| `odoo_env/odooenv.py` | Add `create_test_db()` method (~60 lines), wire dispatch | +60 |
| `odoo_env/managers/environment_manager.py` | Add `discover_modules_in_cwd()` staticmethod (~15 lines), extract `_build_module_command()` (~20 lines), refactor `update()` (~5 line reduction) | +30 |
| `odoo_env/oe.py` | Fix `--create-test-db` help text | +1 |
| `odoo_env/create_database.py` | **Deleted** | -34 |
| `odoo_env/test_oe.py` | Add `TestCreateTestDb` class with ~7 test methods | +120 |
| **Total** | | **~180–210** (well under 400-line budget) |

---

## Testing seams

The design supports strict TDD with `unittest` + `unittest.mock`. Key seams:

### 1. Module discovery
- **Patch**: `os.getcwd()` to control the scanned directory.
- **Patch**: `pathlib.Path.iterdir()` and `pathlib.Path.is_dir()` + `is_file()` to
  simulate directories with/without `__manifest__.py`.
- **Assert**: returned module list matches expected.

### 2. Guard: zero modules abort
- **Patch**: `EnvironmentManager.discover_modules_in_cwd()` to return `[]`.
- **Assert**: `OeError` is raised with message containing "no modules".
- **Assert**: No Command objects are created (no docker, no cp).

### 3. Guard: DB exists + interactive confirm
- **Patch**: `OdooEnv._db_exists()` to return `True`.
- **Patch**: `sys.stdin.isatty()` → `True` / `False`.
- **Patch**: `builtins.input()` → `"y"` / `"n"` / raise `EOFError`.
- **Assert**: On `"y"`, commands are built normally. On `"n"`, `OeError` raised.
  On non-tty, `OeError` raised. On EOFError, `OeError` raised.

### 4. Command composition
- **Patch**: `EnvironmentManager.discover_modules_in_cwd()` → `["module_a", "module_b"]`.
- **Patch**: `OdooEnv._db_exists()` → `False` (skip confirmation).
- **Call**: `oe.create_test_db()`.
- **Assert**: returned list has exactly 4 Commands (cp, restore, rm, install).
- **Assert**: cp command is `["cp", f"{backup_dir}/bkp_test/test.zip", f"{backup_dir}/test.zip"]`.
- **Assert**: rm command is `["rm", f"{backup_dir}/test.zip"]`.
- **Assert**: install command contains `"-i"`, `"module_a, module_b"`, `f"{client}_test"`.
- **Assert**: install command does NOT contain `"--test-enable"`.

### 5. Restore arguments
- **Assert**: restore Command uses `BackupManager.restore()` with:
  - `database = "{client}_test"`
  - `backup_file = "test.zip"`
  - `no_deactivate = True`

### 6. Edges
- **Seed missing**: `seed_path.is_file()` → `False`, assert `OeError`.
- **No subdirectories**: `iterdir()` returns empty, assert 0 modules → `OeError`.
- **Hidden dirs / files**: `iterdir()` includes `.git`, assert not in module list.
- **Symlinks to module dirs**: `is_dir()` follows symlinks, assert discovered.

---

## Requirements coverage

| Requirement | Design element | ADR |
|-------------|---------------|-----|
| REQ-CTDB-001 — Trigger and naming | `OdooEnv.create_test_db()` dispatch in `build_commands()`; `database = f"{self.client.name}_test"` | ADR 1 |
| REQ-CTDB-002 — Module discovery CWD only | `EnvironmentManager.discover_modules_in_cwd()` staticmethod | ADR 2 |
| REQ-CTDB-003 — Seed restore via copy-up | Three sequential Commands: cp, BackupManager.restore(), rm | ADR 4 |
| REQ-CTDB-004 — Install with -i, no --test-enable | `_build_module_command(database, modules, "-i")` — `test_enable` not passed | ADR 3 |
| REQ-CTDB-005 — Zero modules abort | `if not modules: msg.err(...)` at build time, before any Command | ADR 6 |
| REQ-CTDB-006 — Existing DB confirmation | `_db_exists()` + `_confirm_overwrite()` at build time; `isatty()` guard + `input()` | ADR 5 |
| REQ-CTDB-007 — Order of operations | Guards at build time abort before Command list; execute() runs Commands sequentially (cp→restore→rm→install) | ADR 6 |
| Dead-code removal | Delete `odoo_env/create_database.py` (zero callers) | ADR 7 |
| --create-test-db help text | `oe.py:179` help changed from "Create database with demo data" to "Create a test database with all project modules" | ADR 1 |
