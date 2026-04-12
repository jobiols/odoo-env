# Exploration: docker-network-idempotent

## Executive Summary

When `oe -R -c <client>` runs, `EnvironmentManager.run_environment()` always appends a plain `Command` wrapping `["docker", "network", "create", "odoo-net"]`. If the Docker network already exists (from a previous session), Docker exits non-zero with "network already exists," causing the command to fail. The fix is to introduce a new `Command` subclass — `EnsureNetworkCommand` — that overrides `check_args()` to run `docker network inspect odoo-net` (suppressing stdout/stderr), returning `False` (skip) if exit code is 0 and `True` (proceed) if non-zero. This follows the exact same idempotency pattern already used by `MakedirCommand` and `CloneRepo`.

---

## Current Implementation

### `docker_client.py` (line 183–184)
```python
@staticmethod
def get_network_create_command(network: str) -> str:   # BUG: should be -> list[str]
    return ["docker", "network", "create", network]
```

### `environment_manager.py` (lines 130–148)
```python
# Network TODO (existing comment already points to the fix)
cmd_str = self.docker_client.get_network_create_command("odoo-net")
ret.append(
    Command(
        self.parent,
        command=cmd_str,
        usr_msg="Starting odoo-net network if needed",
    )
)
```
No `args=` is passed → `Command.check()` always returns `True` → command always runs.

### `Command.check()` logic (lines 31–38)
```python
def check(self):
    if not self._args:   # no args -> always runs
        return True
    return self.check_args()
```

---

## Pattern Analysis: Idempotency via `check_args()`

| Subclass | `_args` content | `check_args()` logic | Effect |
|---|---|---|---|
| `MakedirCommand` | directory path | `not os.path.isdir(self._args)` | Skip if dir exists |
| `RemovedirCommand` | directory path | `os.path.isdir(self._args)` | Skip if dir absent |
| `CloneRepo` | directory path | `not os.path.isdir(self._args)` | Skip if dir exists |
| `PullRepo` | directory path | `os.path.isdir(self._args)` | Skip if dir absent |
| `CreateNginxTemplate` | file path | `not os.path.isfile(self._args)` | Skip if file exists |

New pattern: `EnsureNetworkCommand` checks Docker state via subprocess instead of filesystem — matches the existing `TODO` comment in `environment_manager.py`.

---

## Docker Inspect Approach

```
docker network inspect odoo-net
  exit code 0    → network exists → check_args() returns False → command skipped
  exit code != 0 → network absent → check_args() returns True  → command runs
```

Use `subprocess.DEVNULL` to suppress output (clean, avoids polluting stdout/stderr).

---

## Scope of Change

1. **`odoo_env/command.py`** — Add `EnsureNetworkCommand(Command)` class
2. **`odoo_env/managers/environment_manager.py`** — Import + use `EnsureNetworkCommand` instead of bare `Command`
3. **`odoo_env/services/docker_client.py`** — Fix type annotation `-> str` → `-> list[str]` (minor, pre-existing bug)
4. **`odoo_env/test_oe.py`** — Add tests for the new command (check_args behavior mocking subprocess.run)

---

## Risks and Edge Cases

1. **`subprocess` import**: Already present in `command.py` (line 2). No new import needed.
2. **`check_args()` via subprocess**: New pattern (existing ones are pure filesystem). Unavoidable for Docker state. The existing `TODO` explicitly endorses this approach.
3. **Type annotation bug**: `get_network_create_command` annotated `-> str` but returns `list[str]`. Fix in scope.
4. **Network name hardcoded**: `"odoo-net"` is hardcoded in `run_environment()` — pre-existing, out of scope.
5. **Docker not running**: Non-zero exit from inspect = treat as "absent, proceed to create" — consistent with how `docker network create` would also fail in that case.
6. **Suppressing output**: Use `subprocess.DEVNULL` directly in `check_args()`, not `subprocess_call()` with `capture=True`.
7. **`EnsureNetworkCommand` import**: Must be added in `environment_manager.py` imports.
