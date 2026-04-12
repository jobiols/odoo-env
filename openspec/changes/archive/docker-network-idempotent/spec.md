# Spec: docker-network-idempotent

**Change**: docker-network-idempotent
**Status**: draft
**Date**: 2026-04-12
**References**: explore.md, proposal.md

---

## 1. Purpose

`EnvironmentManager.run_environment()` currently appends a bare `Command` to
create the `odoo-net` Docker network. Because no `args=` are supplied, the
command always runs — even when the network already exists. Docker then exits
non-zero with "network already exists", breaking the run sequence.

This spec defines the requirements for making the network-creation step
**idempotent**: it MUST run only when the network is absent, and MUST be
silently skipped when it already exists.

---

## 2. Definitions

| Term | Meaning |
|------|---------|
| **network exists** | `docker network inspect odoo-net` exits with code 0 |
| **network absent** | `docker network inspect odoo-net` exits with code non-zero |
| **skip** | `check_args()` returns `False`; the command body is not executed |
| **proceed** | `check_args()` returns `True`; the command body executes normally |
| **DEVNULL** | `subprocess.DEVNULL` — both stdout and stderr are discarded |

---

## 3. Functional Requirements

### FR-1 — `EnsureNetworkCommand` class

**FR-1.1** A new class `EnsureNetworkCommand(Command)` MUST be defined in
`odoo_env/command.py`.

**FR-1.2** `EnsureNetworkCommand` MUST override `check_args()` and MUST NOT
override `execute()` (it inherits the base `Command.execute()` unchanged).

**FR-1.3** `EnsureNetworkCommand` MUST carry a docstring that documents:
- what subprocess is called and why
- the return-value semantics (`False` = skip, `True` = proceed)

**FR-1.4** `EnsureNetworkCommand` MUST accept the network name via the `args=`
parameter of the base `Command.__init__()`, consistent with how `MakedirCommand`,
`CloneRepo`, and `CreateNginxTemplate` supply their filesystem paths.

### FR-2 — `check_args()` behavior

**FR-2.1** When `check_args()` is called, it MUST invoke:

```
subprocess.run(
    ["docker", "network", "inspect", self._args],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
```

`shell=True` MUST NOT be used.

**FR-2.2** If the exit code is **0** (network exists), `check_args()` MUST
return `False` (skip creation).

**FR-2.3** If the exit code is **non-zero** (network absent or Docker not
running), `check_args()` MUST return `True` (proceed to creation).

**FR-2.4** `check_args()` MUST NOT raise an exception for any exit code
returned by `docker network inspect`.

**FR-2.5** `check_args()` MUST NOT suppress or catch errors from the
subsequent `docker network create` call — error propagation remains the
responsibility of `Command.execute()` via `subprocess_call(check=True)`.

### FR-3 — Integration in `run_environment()`

**FR-3.1** `environment_manager.py` MUST import `EnsureNetworkCommand` from
`odoo_env.command`.

**FR-3.2** The `EnsureNetworkCommand` instance MUST be the **first** element
appended to the command list returned by `run_environment()`.

**FR-3.3** The instantiation MUST follow this signature:

```python
EnsureNetworkCommand(
    self.parent,
    command=self.docker_client.get_network_create_command("odoo-net"),
    usr_msg="Starting odoo-net network if needed",
    args="odoo-net",
)
```

**FR-3.4** The existing bare `Command(...)` instantiation for the network step
MUST be removed, along with its associated `TODO` comment block.

### FR-4 — Type annotation fix

**FR-4.1** `DockerClient.get_network_create_command` in
`odoo_env/services/docker_client.py` MUST have its return annotation corrected
from `-> str` to `-> list[str]`. No behavioural change is required.

---

## 4. Scenarios (Given/When/Then)

### SC-01 — Network already exists: creation is skipped

```
Given  run_environment() is called for a client
And    "docker network inspect odoo-net" exits with code 0
When   the command list is executed
Then   "docker network create odoo-net" is NOT called
And    no Docker error is raised
And    the rest of the command sequence continues normally
```

### SC-02 — Network absent: creation runs normally

```
Given  run_environment() is called for a client
And    "docker network inspect odoo-net" exits with code 1 (or any non-zero)
When   the command list is executed
Then   "docker network create odoo-net" IS called
And    the network is created successfully
And    the rest of the command sequence continues normally
```

### SC-03 — `check_args()` returns False when network exists

```
Given  an EnsureNetworkCommand instance with args="odoo-net"
And    subprocess.run is mocked to return exit code 0
When   check_args() is called
Then   the return value is False
And    subprocess.run was called with
         ["docker", "network", "inspect", "odoo-net"]
         stdout=subprocess.DEVNULL
         stderr=subprocess.DEVNULL
         shell=False (default)
```

### SC-04 — `check_args()` returns True when network is absent

```
Given  an EnsureNetworkCommand instance with args="odoo-net"
And    subprocess.run is mocked to return exit code 1
When   check_args() is called
Then   the return value is True
And    subprocess.run was called with
         ["docker", "network", "inspect", "odoo-net"]
         stdout=subprocess.DEVNULL
         stderr=subprocess.DEVNULL
         shell=False (default)
```

### SC-05 — Docker daemon not running: inspect fails, create is attempted

```
Given  an EnsureNetworkCommand instance with args="odoo-net"
And    subprocess.run (inspect) returns exit code non-zero (daemon not running)
When   check_args() is called
Then   the return value is True  (proceed — treat as absent)
And    no exception is raised by check_args()
And    when Command.execute() subsequently runs "docker network create odoo-net"
       that call fails with a clear Docker error message
And    the Docker error is NOT suppressed — it propagates to the caller
```

---

## 5. Non-Functional Requirements

**NFR-1** `shell=True` MUST NOT be used in any subprocess call introduced by
this change, consistent with existing project standards.

**NFR-2** Docker errors other than the "network already exists" scenario MUST
NOT be suppressed. Only `docker network inspect` stdout/stderr are silenced
(via `DEVNULL`); all `docker network create` errors propagate normally.

**NFR-3** `EnsureNetworkCommand` SHOULD carry a docstring on the class and on
`check_args()` documenting the subprocess side effect, so future developers
understand why `check_args()` spawns a process instead of doing a filesystem
check.

**NFR-4** The new class MUST be testable in isolation without a running Docker
daemon by mocking `subprocess.run`.

**NFR-5** All existing tests MUST continue to pass after this change (no
regressions).

---

## 6. Test Requirements

The following unit tests MUST be added to `odoo_env/test_oe.py` (stdlib
`unittest`, no pytest):

| Test name | Mock | Expected |
|-----------|------|----------|
| `test_ensure_network_skips_when_exists` | `subprocess.run` → `returncode=0` | `check_args()` returns `False` |
| `test_ensure_network_runs_when_absent` | `subprocess.run` → `returncode=1` | `check_args()` returns `True` |

Both tests MUST verify that `subprocess.run` was called with the correct
argument list and with `shell` not set to `True`.

---

## 7. Out of Scope

- Parameterizing the network name: `"odoo-net"` remains hardcoded in
  `run_environment()`. This is a pre-existing constraint.
- Changes to any other command in `run_environment()`.
- Changes to `options.py`, `oe.py`, `odoo_env.py`, `backup_manager.py`, or
  any other `Command` subclass not related to network creation.
- Adding retry logic or health-check polling for the Docker daemon.

---

## 8. Files Affected

| File | Change type |
|------|-------------|
| `odoo_env/command.py` | Add `EnsureNetworkCommand` class |
| `odoo_env/managers/environment_manager.py` | Import + use `EnsureNetworkCommand`; remove bare `Command` + TODO block |
| `odoo_env/services/docker_client.py` | Fix `-> str` annotation to `-> list[str]` |
| `odoo_env/test_oe.py` | Add two unit tests |

---

## 9. Definition of Done

- [ ] `EnsureNetworkCommand` class exists in `command.py` with a docstring and
      a `check_args()` that calls `docker network inspect` without `shell=True`.
- [ ] `check_args()` returns `False` when exit code is 0; `True` when non-zero.
- [ ] `environment_manager.py` uses `EnsureNetworkCommand` as the first command
      in the returned list; the bare `Command` and `TODO` comment are removed.
- [ ] `docker_client.py` annotation corrected to `-> list[str]`.
- [ ] Two unit tests added and passing: network-exists branch and network-absent
      branch.
- [ ] All pre-existing tests still pass (`15/15` or current baseline).
- [ ] Manual smoke test: `oe -R -c <client>` does not fail when `odoo-net`
      already exists.
