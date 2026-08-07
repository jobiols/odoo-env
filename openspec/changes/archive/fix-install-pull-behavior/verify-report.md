# Verify Report: fix-install-pull-behavior

**Status**: PASS
**Date**: 2026-04-12
**Change**: fix-install-pull-behavior
**Verifier**: sdd-verify sub-agent

---

## Executive Summary

All 11 requirements are fully satisfied. All 28 tests pass (11 new + 17 existing). Zero
regressions. The implementation correctly follows the command-pattern contract (managers
return `list[Command]`, never execute directly). TDD mode was respected: tests exist for
every requirement and all are green.

---

## Test Suite Results

```
Ran 28 tests in 0.272s
OK
```

All 11 specified tests present and green:

| Test | Result |
|------|--------|
| `TestDockerClient.test_get_pull_command_returns_docker_pull_image` | PASS |
| `TestDockerClient.test_get_pull_command_does_not_contain_run` | PASS |
| `TestDockerClient.test_get_pull_command_has_no_flags` | PASS |
| `TestImageManager.test_pull_images_uses_pull_not_run` | PASS |
| `TestImageManager.test_pull_images_command_starts_with_docker_pull` | PASS |
| `TestImageManager.test_pull_images_calls_extract_sources_in_debug_mode` | PASS |
| `TestImageManager.test_pull_images_no_extract_sources_in_non_debug_mode` | PASS |
| `TestEnvironmentManager.test_install_never_calls_extract_sources` | PASS |
| `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_debug_mode` | PASS |
| `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_non_debug_mode` | PASS |
| `TestEnvironmentManager.test_install_does_not_reference_dist_dirs` | PASS |

---

## Requirement-by-Requirement Verification

### REQ-01 — `get_pull_command` returns `["docker", "pull", image]`
**Status**: PASS

`DockerClient.get_pull_command` at line 130–131 of `services/docker_client.py`:
```python
def get_pull_command(self, image: str) -> list[str]:
    return ["docker", "pull", image]
```
Test `test_get_pull_command_returns_docker_pull_image` asserts the exact return value
`["docker", "pull", "postgres:17.5-alpine"]` and passes.

---

### REQ-02 — `get_pull_command` must not contain the token `"run"`
**Status**: PASS

The implementation returns a three-element list `["docker", "pull", image]` — the string
`"run"` is never included. Test `test_get_pull_command_does_not_contain_run` asserts
`assertNotIn("run", result)` and passes.

---

### REQ-03 — `get_pull_command` must not contain any flags (plain three-element list)
**Status**: PASS

Return value is always `["docker", "pull", image]` with exactly 3 elements and no
optional flags. Test `test_get_pull_command_has_no_flags` asserts `len(result) == 3`
and the exact list content. Passes.

---

### REQ-04 — `pull_images()` uses `get_pull_command`, not `get_run_command`
**Status**: PASS

`ImageManager.pull_images()` at line 19 of `managers/image_manager.py`:
```python
cmd_list = self.docker_client.get_pull_command(image.name)
```
No call to `get_run_command` exists in the pull loop. Test
`test_pull_images_uses_pull_not_run` patches both methods and asserts
`mock_pull.assert_called()` and `mock_run.assert_not_called()`. Passes.

---

### REQ-05 — `pull_images()` returns Commands starting with `["docker", "pull"]`
**Status**: PASS

The `Command` wrapping `get_pull_command`'s output guarantees `.command[:2] == ["docker",
"pull"]`. Test `test_pull_images_command_starts_with_docker_pull` asserts this on the
first returned command. Also verified by `test_oe.TestRepository.test_pull_images` which
asserts the complete first command is `["docker", "pull", "jobiols/odoo-jeo:9.0"]`.

---

### REQ-06 — `pull_images()` appends `extract_sources()` commands when `debug=True`
**Status**: PASS

Lines 27–28 of `managers/image_manager.py`:
```python
if self.parent.debug:
    ret.extend(self.extract_sources())
```
`extract_sources()` produces `rm -rf` removal commands for each pack directory.
Test `test_pull_images_calls_extract_sources_in_debug_mode` sets `debug=True` and asserts
`any("rm" in c.command for c in cmds)`. Passes.

---

### REQ-07 — `pull_images()` omits `extract_sources()` commands when `debug=False`
**Status**: PASS

When `self.parent.debug` is `False`, the `if` block is skipped entirely. Test
`test_pull_images_no_extract_sources_in_non_debug_mode` iterates all commands and asserts
neither `"rm"` nor `"mkdir"` appears in any `.command`. Passes.

---

### REQ-08 — `install()` never calls `extract_sources()` or `do_extract_sources()`
**Status**: PASS

`EnvironmentManager.install()` (lines 33–101) contains no reference to `extract_sources`
or `do_extract_sources`. The method ends with `return ret` after
`ret.extend(self.parent._process_repos())` with no debug-conditional extract block.
Test `test_install_never_calls_extract_sources` patches `OdooEnv.do_extract_sources` and
asserts `mock_extract.assert_not_called()` with `debug=True`. Passes.

---

### REQ-09 — `install()` produces no `rm -rf` commands in debug mode
**Status**: PASS

Since `extract_sources()` is not called from `install()`, no `rm -rf` commands can appear
in its output. Test `test_install_does_not_call_extract_sources_in_debug_mode` with
`debug=True` iterates all returned commands and asserts
`not ("rm" in c.command and "-rf" in c.command)` for each. Passes.

---

### REQ-10 — `install()` produces no `rm -rf` commands in non-debug mode
**Status**: PASS

Symmetric with REQ-09. Test
`test_install_does_not_call_extract_sources_in_non_debug_mode` with `debug=False`
applies the same assertion. Passes. (This was already true before the fix, so the test
is a regression guard.)

---

### REQ-11 — `install()` is idempotent; no reference to `dist-packages` or `dist-local-packages`
**Status**: PASS

`install()` does not call `extract_sources()` and does not call `_get_debug_mountings()`
(that is only called from `run_client()`). Therefore no path containing `dist-packages`
or `dist-local-packages` is referenced in any command produced by `install()`. Test
`test_install_does_not_reference_dist_dirs` with `debug=True` asserts the string absence
across all returned commands. Passes.

---

## TASK Checklist Completion

| Task | Expected outcome | Verified |
|------|-----------------|----------|
| TASK-01 | `test_docker_client.py` with 3 tests | Done |
| TASK-02 | `get_pull_command` implemented in `DockerClient` | Done |
| TASK-03 | `test_image_manager.py` with 4 tests | Done |
| TASK-04 | `pull_images()` uses `get_pull_command` | Done |
| TASK-05 | `test_pull_images` in `test_oe.py` asserts `["docker", "pull", ...]` | Done (line 282) |
| TASK-06 | `test_environment_manager.py` with 4 tests | Done |
| TASK-07 | `do_extract_sources` block removed from `install()` | Done |
| TASK-08 | `test_download_image_sources` redirected to `pull_images()` | Done (line 359) |
| TASK-09 | Full suite passes with 0 failures | Done — 28/28 |

---

## Findings

No CRITICAL or WARNING findings. One SUGGESTION below.

### SUGGESTION (optional)

**test_image_manager.py — `mock_run` scope in REQ-04 test**

The `mock_run` patch on `get_run_command` in `test_pull_images_uses_pull_not_run` is
broad: it patches the method at the class level, which means the `extract_sources()` path
(which calls `get_run_command` for the docker-run-entrypoint command) would also be
suppressed if it were triggered. Since `debug=False` in that test, `extract_sources()` is
not called — so the test is correct and non-fragile today. However, a future refactor that
changes the debug default could silently mask a bug. Consider adding an explicit comment
in the test explaining why `debug=False` is required for the `mock_run.assert_not_called`
assertion to be meaningful.

This is cosmetic. It does not affect correctness.

---

## Artifacts

- `openspec/changes/fix-install-pull-behavior/verify-report.md` (this file)

## Files Verified

- `odoo_env/services/docker_client.py` — `get_pull_command` implemented correctly
- `odoo_env/managers/image_manager.py` — `pull_images()` uses `get_pull_command`; `extract_sources()` appended in debug mode only
- `odoo_env/managers/environment_manager.py` — `install()` contains no extract-sources call
- `odoo_env/test_docker_client.py` — 3 tests (REQ-01 to REQ-03)
- `odoo_env/test_image_manager.py` — 4 tests (REQ-04 to REQ-07)
- `odoo_env/test_environment_manager.py` — 4 tests (REQ-08 to REQ-11)
- `odoo_env/test_oe.py` — `test_pull_images` and `test_download_image_sources` updated
