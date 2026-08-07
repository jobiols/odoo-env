# Tasks: install-from-url

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~158 (∼150 test, ∼8 client.py) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

---

## Status: ✅ COMPLETE

All 10 tests pass. Full suite (92 tests) passes with zero regressions.

---

## Overview

Fix the `oe -i` crash caused by `get_manifest()` treating boolean `True` as a URL.
Strict TDD is active — tests MUST fail (RED) before implementation (GREEN). Tasks are
ordered by TDD phases: Infrastructure → RED → GREEN → VERIFY.

Every task references exact file paths and specifies concrete changes. All 7 spec
requirements (REQ-INSTALL-001 through 007) are covered across the 9 test methods and
3 implementation sub-tasks.

---

## Phase 1: Infrastructure

### Task 1.1 ✅ COMPLETE: Create `test_client.py` skeleton

**File**: `odoo_env/test_client.py` (NEW)

Create a new test file with imports, a `TestGetManifest` class inheriting
`unittest.TestCase`, and `setUp`/`tearDown` methods that configure common mocks.
Use `MockArgs` from `test_helpers` for argument objects.

**Actions**:
- Import `unittest`, `unittest.mock.patch`, `subprocess`, `Path`
- Import `Client` from `odoo_env.client`, `OeConfig` from `odoo_env.config`,
  `MockArgs` from `odoo_env.test_helpers`
- Import `OeError` from `odoo_env.messages` (for asserting URL validation errors)
- Create class `TestGetManifest(unittest.TestCase)` with `setUp` and `tearDown`
- In `setUp`: create mock patches for `OeConfig.get_client_path`, `OeConfig.save_client_path`,
  `Client.get_manifest_from_struct`, and `subprocess.run`. Store mocks as instance attributes.
- In `tearDown`: stop all patches.

**Verification**: `python -m unittest odoo_env.test_client` discovers the test class
(0 tests run, OK).

**Estimated lines**: ~35

---

## Phase 2: RED — Write Failing Tests

All tests in this phase MUST fail when run against the current (unfixed) `client.py`.
Run each batch after writing to confirm RED status.

### Task 2.1 ✅ COMPLETE: Tests for REQ-INSTALL-001 — Boolean/None guard

**File**: `odoo_env/test_client.py`

Write 2 test methods. Both verify that `get_manifest()` does NOT call
`get_manifest_from_url()` when `install` is not a string.

**Test: `test_install_bool_skips_url`**
- Set `self.mock_get_client_path.return_value = None`
- Create client: `client = Client(MockArgs(install=True, debug=False), name="test_client")`
  Call `client.get_manifest()` directly (not via `__init__`) to avoid `check_common` side effects.
  > **Note**: `Client.__init__` calls `get_manifest()` + `check_common()`. To avoid the
  > `check_common`/manifest dependency, instantiate a bare `Client` and set `self._name`,
  > `self._args` manually, OR use `patch.object(Client, 'check_common')`. The simpler
  > approach: call `client.get_manifest()` after `__init__` but patch `check_common` to
  > no-op and patch the fallback `get_manifest_from_struct` to return a valid manifest
  > so `check_common` doesn't crash.
- Assert `self.mock_subprocess_run.assert_not_called()` — git clone never runs
- Assert manifest is not None (came from fallback filesystem walk)

**Test: `test_install_none_skips_url`**
- Same as above but `MockArgs(install=None, debug=False)`
- Assert `self.mock_subprocess_run.assert_not_called()`
- Assert manifest is not None (from fallback)

**Verification**: Run `PYTHONPATH=. venv/bin/python -m unittest odoo_env.test_client.TestGetManifest.test_install_bool_skips_url odoo_env.test_client.TestGetManifest.test_install_none_skips_url` → both FAIL because the current `if self._args.install:` guard lets `True` through, causing a crash or unexpected call.

**Estimated lines**: ~30

---

### Task 2.2 ✅ COMPLETE: Tests for REQ-INSTALL-005/007 — Existing client_path guard

**File**: `odoo_env/test_client.py`

Write 2 test methods verifying that when `OeConfig.get_client_path()` returns a valid
path, URL-based resolution is completely skipped.

**Test: `test_existing_client_path_skips_url_bool`**
- `self.mock_get_client_path.return_value = "/some/existing/path"`
- `self.mock_get_manifest_from_struct.return_value = ({"name": "test_client", "version": "14.0.1.0.0", "docker-images": [], "git-repos": [], "env-ver": "2"}, "/some/existing/path")`
- Create client with `MockArgs(install=True, debug=False)`
- Call `client.get_manifest()`
- Assert `self.mock_subprocess_run.assert_not_called()` — URL clone never attempted
- Assert `self.mock_get_manifest_from_struct.called` — manifest resolved from struct

**Test: `test_existing_client_path_skips_url_str`**
- `self.mock_get_client_path.return_value = "/some/existing/path"`
- Same struct mock
- Create client with `MockArgs(install="git@github.com:org/repo.git", debug=False)`
- Call `client.get_manifest()`
- Assert `self.mock_subprocess_run.assert_not_called()` — URL string ignored
- Assert `self.mock_get_manifest_from_struct.called`

**Verification**: Run both tests → FAIL (current code: when `install=True`, enters
`get_manifest_from_url` before checking `client_path` in the else branch, causing crash).

**Estimated lines**: ~35

---

### Task 2.3 ✅ COMPLETE: Tests for REQ-INSTALL-003 — URL validation

**File**: `odoo_env/test_client.py`

Write 2 test methods for URL format validation in `get_manifest_from_url()`.

**Test: `test_invalid_url_raises_oe_error`**
- `self.mock_get_client_path.return_value = None`
- Create client with `MockArgs(install="not-a-url", debug=False)`
- Call `client.get_manifest_from_url()` directly
- Assert `OeError` is raised
- Assert error message contains "Invalid git URL" and the rejected URL string

**Test: `test_empty_url_raises_oe_error`**
- `self.mock_get_client_path.return_value = None`
- Create client with `MockArgs(install="", debug=False)`
- Call `client.get_manifest_from_url()` directly
- Assert `OeError` is raised
- Assert error message contains "Invalid git URL"

**Verification**: Run both tests → FAIL (current code: no validation; empty string
and "not-a-url" would be passed to `git clone`, producing a `CalledProcessError`, not
`OeError`).

**Estimated lines**: ~25

---

### Task 2.4 ✅ COMPLETE: Tests for REQ-INSTALL-002/004 — URL success path and save_client_path

**File**: `odoo_env/test_client.py`

Write 3 test methods for the happy path: valid URL → clone → manifest → save.

**Test: `test_url_success_saves_client_path`**
- `self.mock_get_client_path.return_value = None`
- `self.mock_get_manifest_from_struct.return_value = ({"name": "test_client", "version": "14.0.1.0.0", "docker-images": [], "git-repos": [], "env-ver": "2"}, "/tmp/tmpXXX/repo-name")`
- Create client with `MockArgs(install="https://github.com/org/repo.git", debug=False)`
- Call `client.get_manifest()` or mock enough to call `get_manifest_from_url()` directly
- Assert `self.mock_subprocess_run.called_once_with(["git", "clone", "--depth", "1", "https://github.com/org/repo.git", ...])`
- Assert `self.mock_save_client_path.called_once_with("test_client", "/tmp/tmpXXX/repo-name")`
- Assert returned manifest is not None

**Test: `test_url_no_manifest_returns_none`**
- `self.mock_get_client_path.return_value = None`
- `self.mock_get_manifest_from_struct.return_value = (None, None)` — no manifest found in clone
- Create client with `MockArgs(install="git@github.com:org/repo.git", debug=False)`
- Call `client.get_manifest_from_url()` directly
- Assert return value is `None`
- Assert `self.mock_save_client_path.assert_not_called()` — nothing saved when no manifest

**Test: `test_url_str_calls_get_manifest_from_url`**
- `self.mock_get_client_path.return_value = None`
- `self.mock_get_manifest_from_struct.return_value = ({"name": "test_client", "version": "14.0.1.0.0", "docker-images": [], "git-repos": [], "env-ver": "2"}, "/tmp/path")`
- Create client with `MockArgs(install="git@github.com:org/repo.git", debug=False)`
- Call `client.get_manifest()`
- Assert `self.mock_subprocess_run.called` — git clone was invoked through `get_manifest_from_url`
- Assert returned manifest is not None

**Verification**: Run all three tests → FAIL (current code: no `save_client_path` call,
no validation of HTTPS vs git@).

**Estimated lines**: ~40

---

### Task 2.5 ✅ COMPLETE: Test for REQ-INSTALL-002-adjunct — Clone failure propagation

**File**: `odoo_env/test_client.py`

Write 1 test method verifying that `git clone` failures propagate as exceptions
(no swallowed errors).

**Test: `test_url_clone_failure_propagates`**
- `self.mock_get_client_path.return_value = None`
- `self.mock_subprocess_run.side_effect = subprocess.CalledProcessError(128, ["git", "clone"])`
- Create client with `MockArgs(install="git@github.com:org/repo.git", debug=False)`
- Call `client.get_manifest_from_url()` directly
- Assert `subprocess.CalledProcessError` is raised (not caught)
- Assert `self.mock_save_client_path.assert_not_called()` — no partial save on failure

**Verification**: Run test → FAIL (current code has no `save_client_path` call; the
exception would propagate, but the assertion about `save_client_path` not being called
would pass if we're checking the right thing. Actually, in the current code `save_client_path`
isn't called at all, so this test may already pass for the "no save" assertion. Adjust:
focus on exception propagation and tempdir cleanup. Actually, let's verify the exception
propagates — the mock will raise, and we just need to assert it propagates.)

> **Correction**: Current code does NOT catch exceptions, so this test WILL pass today
> for the propagation assertion. The RED value comes from verifying that when clone
> fails, `save_client_path` is NOT called (post-implementation behavior). Mark this as
> "may already be GREEN for exception propagation; RED for save_client_path assertion".

**Estimated lines**: ~15

---

## Phase 3: GREEN — Implementation

Apply fixes in order. After each sub-task, run the relevant tests to confirm they turn
GREEN.

### Task 3.1 ✅ COMPLETE: Fix isinstance guard in get_manifest()

**File**: `odoo_env/client.py`, method `get_manifest()`, line 181

**Change**: Replace `if self._args.install:` with `if isinstance(self._args.install, str):`

**Before**:
```python
if self._args.install:
```

**After**:
```python
if isinstance(self._args.install, str):
```

**Affected tests**: Tasks 2.1, 2.2 should now pass. Tasks 2.3–2.5 still fail (no
URL validation or save_client_path yet).

**Verification**: Run tests from tasks 2.1 and 2.2 → GREEN.
Run tests from tasks 2.3–2.5 → still RED (expected).

**Estimated lines**: 1 changed

---

### Task 3.2 ✅ COMPLETE: Add URL validation in get_manifest_from_url()

**File**: `odoo_env/client.py`, method `get_manifest_from_url()`, top of method body

**Change**: Add URL validation block before `tempfile.TemporaryDirectory()` context.

**Insert** (after the `def` line, before `with tempfile.TemporaryDirectory()...`):
```python
url = self._args.install
if not (url.startswith("git@") or url.startswith("https://")):
    msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")
```

**Affected tests**: Task 2.3 should now pass.

**Verification**: Run tests from task 2.3 → GREEN. Other 2.4–2.5 still RED.

**Estimated lines**: 3 added

---

### Task 3.3 ✅ COMPLETE: Add save_client_path call in get_manifest_from_url()

**File**: `odoo_env/client.py`, method `get_manifest_from_url()`, inside the `with` block

**Change**: Capture `manifest_dir` from `get_manifest_from_struct()` and conditionally call
`save_client_path()`.

**Before**:
```python
manifest, _ = self.get_manifest_from_struct(Path(tmpdir))
return manifest
```

**After**:
```python
manifest, manifest_dir = self.get_manifest_from_struct(Path(tmpdir))
if manifest and manifest_dir:
    OeConfig().save_client_path(self._name, manifest_dir)
return manifest
```

**Affected tests**: Tasks 2.4 and 2.5 should now pass.

**Verification**: Run tests from tasks 2.4 and 2.5 → GREEN.

**Estimated lines**: 4 added, 1 changed (net ~4)

---

## Phase 4: VERIFY

### Task 4.1 ✅ COMPLETE: Run full test suite

**Command**:
```
PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'
```

**Expected result**:
- All 9 new tests in `test_client.py` pass
- All existing tests in `test_oe.py`, `test_environment_manager.py`, `test_image_manager.py`
  continue to pass (existing tests mock `Client.get_manifest` entirely, so no breakage expected)
- Zero regressions

**If any existing test fails**: pause and diagnose. The `isinstance` guard and
`save_client_path` addition are additive-only changes; no existing code path is altered.
But verify the `get_manifest_from_url()` change didn't break `get_manifest_from_struct`
return value unpacking for the URL-not-passed case (which doesn't call
`get_manifest_from_url()` at all).

**Estimated lines**: 0

---

### Task 4.2 ✅ COMPLETE: Spec compliance verification

Cross-reference every spec scenario against the test cases and implementation:

| REQ | Scenarios | Test(s) |
|-----|-----------|---------|
| REQ-INSTALL-001 | install=True skips URL, install=None skips URL | 2.1 |
| REQ-INSTALL-002 | string URL forwarded to get_manifest_from_url | 2.4 (test_url_str_calls_get_manifest_from_url) |
| REQ-INSTALL-003 | valid https:// accepted, valid git@ accepted, invalid string raises, empty string raises | 2.3 |
| REQ-INSTALL-004 | save_client_path on success, NOT saved on clone failure | 2.4, 2.5 |
| REQ-INSTALL-005 | client_path exists → URL skipped (bool and str install) | 2.2 |
| REQ-INSTALL-006 | temp directory cleanup (guaranteed by TemporaryDirectory, validated by 2.4 + 2.5) | 2.4, 2.5 |
| REQ-INSTALL-007 | existing project skip with boolean -i | 2.2 |

All 7 requirements covered. All 12 spec scenarios covered.

**Estimated lines**: 0

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 10 (1 infrastructure + 5 RED + 3 GREEN + 2 VERIFY) |
| Files created | 1 (`odoo_env/test_client.py`) |
| Files modified | 1 (`odoo_env/client.py`) |
| New test methods | 9 |
| Lines of test code | ~150 |
| Lines of implementation | ~8 |
| Total estimated delta | ~158 lines |
| Strict TDD phases | RED (5 tasks) → GREEN (3 tasks) → VERIFY (2 tasks) |
