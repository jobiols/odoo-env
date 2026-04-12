# Tasks: docker-network-idempotent

**Change**: docker-network-idempotent
**Status**: ready
**Date**: 2026-04-12
**References**: spec.md, proposal.md

---

## Phase 1 — Tests (write first, they MUST fail initially)

### 1.1 — Add import for `EnsureNetworkCommand` in `test_oe.py`

**File**: `odoo_env/test_oe.py`, line 4 (imports block)

Add `EnsureNetworkCommand` to the existing import from `odoo_env.command`:

```python
from odoo_env.command import Command, EnsureNetworkCommand
```

This import will fail with `ImportError` until Phase 2.1 is done — that is expected
(Red phase).

---

### 1.2 — Write `test_ensure_network_skips_when_exists`

**File**: `odoo_env/test_oe.py` — add inside `TestRepository` class, after the
last test method (`test_repo2_clone`, currently line 418).

**What to test** (SC-03):
- Create a minimal mock parent with `verbose=False`.
- Instantiate `EnsureNetworkCommand(parent, command=[...], usr_msg="...", args="odoo-net")`.
- Mock `subprocess.run` (target: `odoo_env.command.subprocess.run`) to return a
  mock object with `returncode=0`.
- Assert `check_args()` returns `False`.
- Assert `subprocess.run` was called with
  `["docker", "network", "inspect", "odoo-net"]`,
  `stdout=subprocess.DEVNULL`, `stderr=subprocess.DEVNULL`.
- Assert `shell` was NOT set to `True` (i.e., it was not passed or was `False`).

Template (expand in place):

```python
def test_ensure_network_skips_when_exists(self):
    """SC-03: check_args() returns False when docker network inspect exits 0."""
    import subprocess as _subprocess

    mock_parent = unittest.mock.MagicMock()
    mock_parent.verbose = False

    cmd = EnsureNetworkCommand(
        mock_parent,
        command=["docker", "network", "create", "odoo-net"],
        usr_msg="Starting odoo-net network if needed",
        args="odoo-net",
    )

    mock_result = unittest.mock.MagicMock()
    mock_result.returncode = 0

    with patch("odoo_env.command.subprocess.run", return_value=mock_result) as mock_run:
        result = cmd.check_args()

    self.assertFalse(result)
    mock_run.assert_called_once_with(
        ["docker", "network", "inspect", "odoo-net"],
        stdout=_subprocess.DEVNULL,
        stderr=_subprocess.DEVNULL,
    )
```

---

### 1.3 — Write `test_ensure_network_runs_when_absent`

**File**: `odoo_env/test_oe.py` — add immediately after 1.2.

**What to test** (SC-04):
- Same setup as 1.2 but `returncode=1`.
- Assert `check_args()` returns `True`.
- Assert `subprocess.run` was called with the same correct args.

Template:

```python
def test_ensure_network_runs_when_absent(self):
    """SC-04: check_args() returns True when docker network inspect exits non-zero."""
    import subprocess as _subprocess

    mock_parent = unittest.mock.MagicMock()
    mock_parent.verbose = False

    cmd = EnsureNetworkCommand(
        mock_parent,
        command=["docker", "network", "create", "odoo-net"],
        usr_msg="Starting odoo-net network if needed",
        args="odoo-net",
    )

    mock_result = unittest.mock.MagicMock()
    mock_result.returncode = 1

    with patch("odoo_env.command.subprocess.run", return_value=mock_result) as mock_run:
        result = cmd.check_args()

    self.assertTrue(result)
    mock_run.assert_called_once_with(
        ["docker", "network", "inspect", "odoo-net"],
        stdout=_subprocess.DEVNULL,
        stderr=_subprocess.DEVNULL,
    )
```

---

### 1.4 — Run the test suite; confirm 2 new tests FAIL (Red)

**Command**:
```
PYTHONPATH=/home/jobiols/tmp/odoo-env \
  /home/jobiols/tmp/odoo-env/venv/bin/python \
  -m unittest discover -s odoo_env -p "test_*.py"
```

Expected outcome: 15 existing tests pass; 2 new tests fail with `ImportError`
(because `EnsureNetworkCommand` does not exist yet). This confirms the tests
are wired correctly and the Red phase is active.

---

## Phase 2 — Implementation

### 2.1 — Add `EnsureNetworkCommand` class to `command.py`

**File**: `odoo_env/command.py` — insert after `MakedirCommand` (currently
line 120–123), before `RemovedirCommand` (line 126).

Requirements:
- Subclass of `Command`; no `__init__` override needed.
- Class-level docstring explaining:
  - what subprocess is run and why.
  - return-value semantics (`False` = skip, `True` = proceed).
- Override only `check_args()` — do NOT override `execute()`.
- `check_args()` must call:
  ```python
  result = subprocess.run(
      ["docker", "network", "inspect", self._args],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  return result.returncode != 0
  ```
- `shell=True` MUST NOT appear.
- `check_args()` must carry its own docstring.

Full class to insert:

```python
class EnsureNetworkCommand(Command):
    """
    Creates a Docker network only when it does not yet exist.

    check_args() runs 'docker network inspect <network>' via subprocess.run
    (no shell=True) to probe whether the network is present:
      - returncode 0  → network exists → return False (skip creation)
      - returncode ≠ 0 → network absent → return True  (proceed to create)

    execute() is inherited from Command unchanged; it runs the
    'docker network create <network>' command passed via command=.
    """

    def check_args(self) -> bool:
        """
        Returns False when the network already exists (skip creation),
        True when it is absent (proceed to create).

        Side effect: spawns 'docker network inspect self._args' with both
        stdout and stderr discarded so no Docker output reaches the user.
        Does NOT raise for any exit code from docker network inspect.
        """
        result = subprocess.run(
            ["docker", "network", "inspect", self._args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode != 0
```

---

### 2.2 — Run tests; confirm 2 new tests PASS (Green)

**Command**: same as 1.4.

Expected outcome: all 17 tests pass (15 existing + 2 new). If any existing test
breaks, stop and diagnose before continuing.

---

### 2.3 — Fix type annotation in `docker_client.py`

**File**: `odoo_env/services/docker_client.py`, line 183.

Change:
```python
def get_network_create_command(network: str) -> str:
```
to:
```python
def get_network_create_command(network: str) -> list[str]:
```

No behavioral change — annotation only. Run tests again to confirm 17/17 still
pass.

---

### 2.4 — Update `environment_manager.py`: import + swap call site

**File**: `odoo_env/managers/environment_manager.py`

**Step A — Add import** (line 1, existing import block):
```python
from odoo_env.command import (
    Command,
    CreateNginxTemplate,
    EnsureNetworkCommand,   # add this line
    MakedirCommand,
)
```

**Step B — Replace the bare `Command` network block** (currently lines 132–148):

Remove the entire `# Network TODO` comment block (lines 132–139) and the
`cmd_str = ...` / `ret.append(Command(...))` block (lines 141–148).

Replace with:
```python
# Network — create only if absent
ret.append(
    EnsureNetworkCommand(
        self.parent,
        command=self.docker_client.get_network_create_command("odoo-net"),
        usr_msg="Starting odoo-net network if needed",
        args="odoo-net",
    )
)
```

The first element of `ret` must now be the `EnsureNetworkCommand` instance
(FR-3.2).

---

### 2.5 — Run full test suite; confirm 17/17 pass (Green — final)

**Command**: same as 1.4.

Expected: 17 tests pass, 0 failures, 0 errors.

---

## Phase 3 — Cleanup

### 3.1 — Review `command.py` insertion point and surrounding code

**File**: `odoo_env/command.py`

Verify:
- `EnsureNetworkCommand` sits logically after `MakedirCommand` and before
  `RemovedirCommand` (similar "existence check" commands grouped together).
- Docstrings read naturally for a developer unfamiliar with the change.
- No trailing whitespace or stray blank lines introduced.

---

### 3.2 — Verify the TODO comment block is fully removed in `environment_manager.py`

**File**: `odoo_env/managers/environment_manager.py`

Confirm that lines containing the old `# Network TODO` block and the original
`Command(...)` call for the network step are gone. Search for `TODO` in the
network area to make sure nothing was left behind.

---

### 3.3 — Final test run to confirm no regressions

**Command**: same as 1.4.

All 17 tests must pass. This is the gate before verification.

---

## Phase 4 — Verification

### 4.1 — Run all tests and confirm 15 + 2 = 17 pass

```
PYTHONPATH=/home/jobiols/tmp/odoo-env \
  /home/jobiols/tmp/odoo-env/venv/bin/python \
  -m unittest discover -s odoo_env -p "test_*.py" -v
```

Expected output (verbose):
- `test_ensure_network_skips_when_exists` … OK
- `test_ensure_network_runs_when_absent` … OK
- All 15 pre-existing tests … OK
- Ran 17 tests in X.XXXs — OK

---

### 4.2 — Manual smoke test

Precondition: Docker daemon is running and the `odoo-net` network already exists
(`docker network ls | grep odoo-net`).

Run:
```
oe -R -c <any-configured-client>
```

Expected:
- The "Starting odoo-net network if needed" step is silently skipped (no Docker
  error, no "network already exists" message).
- The rest of the run sequence (postgres, aeroo, etc.) continues normally.
- Exit code 0.

If the network does NOT exist beforehand, run the same command — the network
must be created successfully and postgres must start.

---

## Definition of Done Checklist

- [ ] `EnsureNetworkCommand` class in `odoo_env/command.py` with class + method docstrings.
- [ ] `check_args()` returns `False` (exit code 0) and `True` (exit code ≠ 0) — no `shell=True`.
- [ ] `environment_manager.py` uses `EnsureNetworkCommand` as first element of `ret`; old `Command` + TODO block removed.
- [ ] `docker_client.py` annotation fixed: `-> list[str]`.
- [ ] Two new unit tests in `test_oe.py`: `test_ensure_network_skips_when_exists`, `test_ensure_network_runs_when_absent`.
- [ ] All 17 tests pass (15 pre-existing + 2 new).
- [ ] Manual smoke test: `oe -R -c <client>` does not fail when `odoo-net` already exists.
