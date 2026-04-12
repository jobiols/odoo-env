# Proposal: docker-network-idempotent

## 1. Intent

When `oe -R -c <client>` runs, `EnvironmentManager.run_environment()` always
appends a bare `Command` wrapping `["docker", "network", "create", "odoo-net"]`.
Because `Command.check()` returns `True` when no `args` are supplied, the
command always executes — even when the network already exists. Docker exits
non-zero with "network already exists", breaking the run sequence.

The fix makes the network-creation step **idempotent**: it runs only when the
network is absent, and is silently skipped when it already exists. This removes
a spurious failure that hits every user who switches clients without stopping
containers.

---

## 2. Scope

### Files that change

| File | What changes |
|---|---|
| `odoo_env/command.py` | Add `EnsureNetworkCommand(Command)` subclass |
| `odoo_env/managers/environment_manager.py` | Import and use `EnsureNetworkCommand`; remove the `TODO` comment block |
| `odoo_env/services/docker_client.py` | Fix pre-existing type annotation bug: `-> str` → `-> list[str]` on `get_network_create_command` |
| `odoo_env/test_oe.py` | Add unit tests for `EnsureNetworkCommand.check_args()` (both branches: network present / absent) |

### Files that do NOT change

Everything else: `options.py`, `oe.py`, `odoo_env.py`, `backup_manager.py`,
all other `Command` subclasses. The change is contained to the four files above.

---

## 3. Chosen Approach: `EnsureNetworkCommand` subclass

### How it works

A new `Command` subclass is added in `command.py`:

```
class EnsureNetworkCommand(Command):
    # _args: the network name (e.g. "odoo-net")
    # check_args() returns False  → skip (network already exists)
    # check_args() returns True   → proceed (network is absent)
```

`check_args()` calls `docker network inspect <network>` via `subprocess.run`
with `stdout=subprocess.DEVNULL` and `stderr=subprocess.DEVNULL`.
- Exit code 0 → network exists → return `False` (skip creation)
- Exit code non-zero → network absent → return `True` (proceed to create)

In `environment_manager.py`, the existing bare `Command(...)` instantiation is
replaced with:

```python
EnsureNetworkCommand(
    self.parent,
    command=self.docker_client.get_network_create_command("odoo-net"),
    usr_msg="Starting odoo-net network if needed",
    args="odoo-net",
)
```

The `args="odoo-net"` string is what activates `check_args()` — matching
exactly how `MakedirCommand`, `CloneRepo`, and `CreateNginxTemplate` signal
that a pre-execution check is required.

### Why this approach

- **Follows the established pattern**: every other conditional command in the
  codebase uses `check_args()`. A new subclass is the conventional extension
  point. Adding a subclass leaves zero ambiguity: the class name documents the
  intent.
- **No `shell=True`**: stays consistent with the project standard of passing
  command lists to `subprocess`.
- **Testable in isolation**: `check_args()` can be unit-tested by mocking
  `subprocess.run` — no Docker daemon required in CI.
- **The `TODO` comment in `environment_manager.py` (lines 132–139) already
  endorses this exact design**; the exploration confirms `subprocess` is already
  imported in `command.py` (line 2).

---

## 4. Alternatives Considered

### A) Shell `|| true` — rejected

Passing `"docker network create odoo-net || true"` as a shell string requires
`shell=True` in `subprocess.run`. The project standard explicitly forbids
`shell=True` (documented in Project Standards). Additionally, `|| true` masks
all errors, including genuine failures (e.g. Docker daemon not running), making
debugging much harder.

**Verdict**: violates project constraints and is too blunt an error suppressor.

### B) Inline `--if-not-exists`-style guard in `environment_manager.py` — rejected

This means adding an `if`-block inside `run_environment()` that calls
`docker network inspect` before deciding whether to append the command. It
works, but it breaks the separation of concerns: `check_args()` is the
designated location for "should this command run?" logic. Putting a subprocess
call directly in the manager mixes orchestration logic with execution logic,
makes the condition invisible to the `Command.check()` gate, and cannot be
unit-tested through the normal `Command` interface.

**Verdict**: functional but architecturally inconsistent with the established
pattern.

### C) Catch the Docker non-zero exit in `subprocess_call` — rejected

Wrapping the existing bare `Command` with `check=False` and inspecting the
stderr string for "already exists" couples error handling to a Docker-specific
error message string, which is fragile. It also means the command always
executes and always logs to the user, even when nothing needed to be done.

**Verdict**: fragile, poor UX, and harder to test.

---

## 5. Rollback Plan

The change is additive (new subclass) plus one call-site swap. Rollback is a
two-step revert:

1. In `environment_manager.py`: replace `EnsureNetworkCommand(...)` with the
   original `Command(...)` (no `args=`).
2. In `command.py`: delete the `EnsureNetworkCommand` class.
3. In `docker_client.py`: revert the type annotation if needed (low risk —
   annotation-only change).
4. Delete the new tests from `test_oe.py`.

Because no database schemas, configuration files, or external systems are
touched, rollback carries zero risk of data loss.

---

## 6. Risks

### R1 — Docker daemon not running at check time (low impact)

If Docker is not running, `docker network inspect` exits non-zero. `check_args()`
returns `True`, so `docker network create` runs — and also fails, but with a
clear Docker error message. This is the same behavior as today; the change does
not make this scenario worse.

**Mitigation**: no special handling needed. The existing error propagation in
`subprocess_call(check=True)` already surfaces the Docker error to the user.

### R2 — Network name hardcoded as `"odoo-net"` (pre-existing, out of scope)

Both the `args=` value and the `get_network_create_command("odoo-net")` call
pass a literal string. This is a pre-existing constraint and is not introduced
by this change.

**Mitigation**: noted for future work; not addressed here to keep scope minimal.

### R3 — Subprocess in `check_args()` is a new pattern

All current `check_args()` implementations are pure filesystem checks
(`os.path.isdir`, `os.path.isfile`). Calling a subprocess in `check_args()` is
new. If future developers add logging or side effects to `check_args()`, they
may not expect it to spawn a process.

**Mitigation**: add a docstring to `EnsureNetworkCommand.check_args()` clearly
documenting that it runs `docker network inspect` and why. The class name itself
(`EnsureNetwork`) signals non-trivial semantics.

---

## 7. Definition of Done

- [ ] `EnsureNetworkCommand` class exists in `odoo_env/command.py` with a
      `check_args()` that calls `docker network inspect` and returns the correct
      boolean for each exit code branch.
- [ ] `environment_manager.py` uses `EnsureNetworkCommand` (not bare `Command`)
      for the network step; the `TODO` comment block is removed.
- [ ] `docker_client.py` annotation corrected to `-> list[str]`.
- [ ] At least two unit tests in `test_oe.py`:
  - `test_ensure_network_skips_when_exists`: mocks `subprocess.run` with
    exit code 0, asserts `check_args()` returns `False`.
  - `test_ensure_network_runs_when_absent`: mocks `subprocess.run` with
    exit code 1, asserts `check_args()` returns `True`.
- [ ] All existing tests still pass (`15/15`).
- [ ] `oe -R -c <client>` does not fail when the `odoo-net` network already
      exists (manual smoke test or integration test if available).
