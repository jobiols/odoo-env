# Apply Progress: docker-network-idempotent

**Status**: complete
**Date**: 2026-04-12
**Test count**: 17/17 pass

---

## Phase 1 — Tests (Red) — DONE

- Task 1.1: Updated import in `odoo_env/test_oe.py` line 4 to include `EnsureNetworkCommand`.
- Task 1.2: Added `test_ensure_network_skips_when_exists` (SC-03) after `test_repo2_clone`.
- Task 1.3: Added `test_ensure_network_runs_when_absent` (SC-04) immediately after.
- Task 1.4: Confirmed Red — `ImportError: cannot import name 'EnsureNetworkCommand'`. Baseline 15 tests could not load due to import failure at module level (expected).

## Phase 2 — Implementation (Green) — DONE

- Task 2.1: Added `EnsureNetworkCommand(Command)` class to `odoo_env/command.py` between `MakedirCommand` (line 120) and `RemovedirCommand` (line 156). Class and method docstrings present. No `shell=True`. Uses `subprocess.run` with `DEVNULL`. Returns `result.returncode != 0`.
- Task 2.2: Confirmed Green — 17/17 tests pass.
- Task 2.3: Fixed annotation in `odoo_env/services/docker_client.py` line 183: `-> str` → `-> list[str]`. No behavioral change. 17/17 still pass.
- Task 2.4: Updated `odoo_env/managers/environment_manager.py`:
  - Added `EnsureNetworkCommand` to import block.
  - Removed entire `# Network TODO` comment block (lines 132–139) and bare `Command(...)` block (lines 141–148).
  - Replaced with `EnsureNetworkCommand` as first element of `ret`.
- Task 2.5: Confirmed 17/17 pass.

## Phase 3 — Cleanup — DONE

- Task 3.1: Verified `EnsureNetworkCommand` placement in `command.py` — correct position, clean formatting, no trailing whitespace.
- Task 3.2: Verified `TODO` search in `environment_manager.py` — zero matches found.
- Task 3.3: Final test run — 17 tests in 0.079s — OK.

---

## Files Modified

| File | Change |
|------|--------|
| `odoo_env/test_oe.py` | Updated import + added 2 unit tests |
| `odoo_env/command.py` | Added `EnsureNetworkCommand` class |
| `odoo_env/services/docker_client.py` | Fixed `-> str` annotation to `-> list[str]` |
| `odoo_env/managers/environment_manager.py` | Import + swap call site + removed TODO block |

---

## Definition of Done Checklist

- [x] `EnsureNetworkCommand` class in `odoo_env/command.py` with class + method docstrings.
- [x] `check_args()` returns `False` (exit code 0) and `True` (exit code ≠ 0) — no `shell=True`.
- [x] `environment_manager.py` uses `EnsureNetworkCommand` as first element of `ret`; old `Command` + TODO block removed.
- [x] `docker_client.py` annotation fixed: `-> list[str]`.
- [x] Two new unit tests in `test_oe.py`: `test_ensure_network_skips_when_exists`, `test_ensure_network_runs_when_absent`.
- [x] All 17 tests pass (15 pre-existing + 2 new).
- [ ] Manual smoke test: `oe -R -c <client>` does not fail when `odoo-net` already exists. (requires running Docker — out of scope for automated apply)
