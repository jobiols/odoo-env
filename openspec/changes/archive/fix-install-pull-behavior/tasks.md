# Tasks: fix-install-pull-behavior

**Status**: draft
**Date**: 2026-04-12
**Change**: fix-install-pull-behavior
**TDD Mode**: STRICT — tests before implementation, no exceptions

---

## Overview

11 requirements → 11 tests → 3 implementation changes across 3 files.

Layer order (hard dependency):
1. DockerClient (tests → impl)
2. ImageManager (tests → impl)
3. EnvironmentManager (tests → impl)

---

## Layer 1 — DockerClient

### TASK-01: Write failing tests for `get_pull_command` in `test_docker_client.py`

- [ ] TASK-01: Write failing tests for `DockerClient.get_pull_command`
  - File: `odoo_env/test_docker_client.py` (create new)
  - REQ: REQ-01, REQ-02, REQ-03
  - Details:
    - Create file with `import unittest` and `from odoo_env.services.docker_client import DockerClient`
    - No mocking needed — `DockerClient` is a pure value object
    - Class: `TestDockerClient(unittest.TestCase)`
    - No `setUp`/`tearDown` required (no singletons, no I/O)
    - Method `test_get_pull_command_returns_docker_pull_image`:
      ```python
      dc = DockerClient()
      result = dc.get_pull_command("postgres:17.5-alpine")
      self.assertEqual(result, ["docker", "pull", "postgres:17.5-alpine"])
      ```
    - Method `test_get_pull_command_does_not_contain_run`:
      ```python
      dc = DockerClient()
      result = dc.get_pull_command("postgres:17.5-alpine")
      self.assertNotIn("run", result)
      ```
    - Method `test_get_pull_command_has_no_flags`:
      ```python
      dc = DockerClient()
      result = dc.get_pull_command("some-image:tag")
      self.assertEqual(len(result), 3)
      self.assertEqual(result, ["docker", "pull", "some-image:tag"])
      ```
    - Run suite — all 3 tests MUST fail with `AttributeError` (method does not exist yet)

---

### TASK-02: Implement `get_pull_command` in `DockerClient`

- [ ] TASK-02: Add `get_pull_command(image: str) -> list[str]` to `DockerClient`
  - File: `odoo_env/services/docker_client.py`
  - REQ: REQ-01, REQ-02, REQ-03
  - Details:
    - Add after `get_rm_command`, before `get_run_command` (keep public API grouped)
    - Signature: `def get_pull_command(self, image: str) -> list[str]:`
    - Body: `return ["docker", "pull", image]`
    - No flags, no options — plain three-element list
    - Run TASK-01 tests — all 3 MUST now pass

---

## Layer 2 — ImageManager

### TASK-03: Write failing tests for `ImageManager.pull_images()` in `test_image_manager.py`

- [ ] TASK-03: Write failing tests for `ImageManager.pull_images()`
  - File: `odoo_env/test_image_manager.py` (create new)
  - REQ: REQ-04, REQ-05, REQ-06, REQ-07
  - Details:
    - Imports:
      ```python
      import unittest
      from unittest.mock import patch, MagicMock, call
      from odoo_env.config import OeConfig
      from odoo_env.singleton import SingletonMeta
      from odoo_env.odooenv import OdooEnv
      ```
    - Copy `MockArgs` class verbatim from `test_oe.py`
    - Copy `TEST_CLIENT_MANIFEST` verbatim from `test_oe.py`
    - Class: `TestImageManager(unittest.TestCase)`
    - `setUp` MUST:
      1. Reset singleton: `if OeConfig in SingletonMeta._instances: del SingletonMeta._instances[OeConfig]`
      2. Start `patch("odoo_env.config.OeConfig._get_config_data")` returning the standard config dict (same as `test_oe.py`)
      3. Start `patch("odoo_env.config.OeConfig._save_config_data")`
      4. Start `patch("odoo_env.client.Client.get_manifest")` returning `TEST_CLIENT_MANIFEST`
    - `tearDown` MUST stop all patchers
    - Method `test_pull_images_uses_pull_not_run` (REQ-04):
      ```python
      # Patch at the DockerClient instance method level
      with patch("odoo_env.services.docker_client.DockerClient.get_pull_command",
                 return_value=["docker", "pull", "jobiols/odoo-jeo:9.0"]) as mock_pull, \
           patch("odoo_env.services.docker_client.DockerClient.get_run_command") as mock_run:
          options = MockArgs(debug=False, client="test_client")
          oe = OdooEnv(options)
          oe.pull_images()
          mock_pull.assert_called()
          mock_run.assert_not_called()
      ```
    - Method `test_pull_images_command_starts_with_docker_pull` (REQ-05):
      ```python
      options = MockArgs(debug=False, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.pull_images()
      self.assertEqual(cmds[0].command[:2], ["docker", "pull"])
      ```
    - Method `test_pull_images_calls_extract_sources_in_debug_mode` (REQ-06):
      ```python
      self.mock_config_data.return_value["environment"] = "debug"
      options = MockArgs(debug=True, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.pull_images()
      # At least one command in the tail contains "rm" (extract_sources removal step)
      has_rm = any("rm" in c.command for c in cmds)
      self.assertTrue(has_rm, "Expected extract_sources rm commands in debug mode")
      ```
    - Method `test_pull_images_no_extract_sources_in_non_debug_mode` (REQ-07):
      ```python
      options = MockArgs(debug=False, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.pull_images()
      for c in cmds:
          self.assertNotIn("rm", c.command,
              f"Unexpected rm command in non-debug pull_images: {c.command}")
          self.assertFalse(
              c.command and c.command[0] == "mkdir",
              f"Unexpected mkdir command in non-debug pull_images: {c.command}")
      ```
    - Run suite — TASK-03 tests that check for `["docker", "pull", ...]` MUST fail (currently returns `docker run`)
    - `test_pull_images_uses_pull_not_run` will also fail (mock_run IS called currently)

---

### TASK-04: Fix `ImageManager.pull_images()` to use `get_pull_command`

- [ ] TASK-04: Replace `get_run_command` with `get_pull_command` in `pull_images()`
  - File: `odoo_env/managers/image_manager.py`
  - REQ: REQ-04, REQ-05
  - Details:
    - In `pull_images()`, line 19: replace
      ```python
      cmd_list = self.docker_client.get_run_command(image.name)
      ```
      with:
      ```python
      cmd_list = self.docker_client.get_pull_command(image.name)
      ```
    - The `extract_sources()` call in the `if self.parent.debug:` block (lines 27-28) MUST NOT be touched — it remains in place (REQ-06 requires it)
    - Run TASK-03 tests — all 4 MUST now pass

---

### TASK-05: Update existing `test_pull_images` in `test_oe.py` to match new behavior

- [ ] TASK-05: Fix the existing `test_pull_images` test in `test_oe.py`
  - File: `odoo_env/test_oe.py`
  - REQ: REQ-05
  - Details:
    - Line 282: the assertion currently reads:
      ```python
      self.assertEqual(cmds[0].command, ["docker", "run", "jobiols/odoo-jeo:9.0"])
      ```
    - After TASK-04 this assertion will fail because the implementation now returns `["docker", "pull", ...]`
    - Update it to:
      ```python
      self.assertEqual(cmds[0].command, ["docker", "pull", "jobiols/odoo-jeo:9.0"])
      ```
    - Run the full test suite — no regressions must be introduced

---

## Layer 3 — EnvironmentManager

### TASK-06: Write failing tests for `EnvironmentManager.install()` in `test_environment_manager.py`

- [ ] TASK-06: Write failing tests for `EnvironmentManager.install()` no-extract-sources invariants
  - File: `odoo_env/test_environment_manager.py` (create new)
  - REQ: REQ-08, REQ-09, REQ-10, REQ-11
  - Details:
    - Imports:
      ```python
      import unittest
      from unittest.mock import patch, MagicMock
      from odoo_env.config import OeConfig
      from odoo_env.singleton import SingletonMeta
      from odoo_env.odooenv import OdooEnv
      ```
    - Copy `MockArgs` and `TEST_CLIENT_MANIFEST` from `test_oe.py`
    - Class: `TestEnvironmentManager(unittest.TestCase)`
    - `setUp` MUST apply the full mock chain identical to `TestRepository.setUp` in `test_oe.py` (singleton reset + 3 patchers)
    - `tearDown` MUST stop all patchers
    - Method `test_install_never_calls_extract_sources` (REQ-08):
      ```python
      with patch("odoo_env.odooenv.OdooEnv.do_extract_sources") as mock_extract:
          options = MockArgs(debug=True, no_repos=False, nginx=False, client="test_client")
          oe = OdooEnv(options)
          oe.install()
          mock_extract.assert_not_called()
      ```
    - Method `test_install_does_not_call_extract_sources_in_debug_mode` (REQ-09):
      ```python
      self.mock_config_data.return_value["environment"] = "debug"
      options = MockArgs(debug=True, no_repos=False, nginx=False, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.install()
      for c in cmds:
          has_rm_rf = "rm" in c.command and "-rf" in c.command
          self.assertFalse(has_rm_rf,
              f"Found rm -rf command in install() debug mode: {c.command}")
      ```
    - Method `test_install_does_not_call_extract_sources_in_non_debug_mode` (REQ-10):
      ```python
      options = MockArgs(debug=False, no_repos=False, nginx=False, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.install()
      for c in cmds:
          has_rm_rf = "rm" in c.command and "-rf" in c.command
          self.assertFalse(has_rm_rf,
              f"Found rm -rf command in install() non-debug mode: {c.command}")
      ```
    - Method `test_install_does_not_reference_dist_dirs` (REQ-11):
      ```python
      self.mock_config_data.return_value["environment"] = "debug"
      options = MockArgs(debug=True, no_repos=False, nginx=False, client="test_client")
      oe = OdooEnv(options)
      cmds = oe.install()
      for c in cmds:
          cmd_str = " ".join(str(t) for t in c.command)
          self.assertNotIn("dist-packages", cmd_str,
              f"install() references dist-packages: {c.command}")
          self.assertNotIn("dist-local-packages", cmd_str,
              f"install() references dist-local-packages: {c.command}")
      ```
    - Run suite — `test_install_never_calls_extract_sources`, `test_install_does_not_call_extract_sources_in_debug_mode`, and `test_install_does_not_reference_dist_dirs` MUST fail (current code calls `do_extract_sources` in debug mode)
    - `test_install_does_not_call_extract_sources_in_non_debug_mode` will already pass (non-debug never called it)

---

### TASK-07: Remove `do_extract_sources` call from `EnvironmentManager.install()`

- [ ] TASK-07: Delete the `if OeConfig().debug: do_extract_sources(...)` block from `install()`
  - File: `odoo_env/managers/environment_manager.py`
  - REQ: REQ-08, REQ-09, REQ-10, REQ-11
  - Details:
    - Remove lines 101-103 entirely:
      ```python
      # DELETE:
      if OeConfig().debug:
          # Aca se crean los compandos para hacer el exttract souces
          ret.extend(self.parent.do_extract_sources(self._client.name))
      ```
    - `install()` must end with `return ret` immediately after `ret.extend(self.parent._process_repos())`
    - No replacement needed — the extract_sources responsibility belongs to `pull_images()` (already handles it via REQ-06)
    - Run TASK-06 tests — all 4 MUST now pass
    - Run TASK-03 tests — must still pass (extract_sources remains in pull_images)
    - Run full suite (`test_oe.py`) — `test_download_image_sources` will now fail because it tested extract commands appearing in `install()` output

---

### TASK-08: Update `test_download_image_sources` in `test_oe.py` to reflect new behavior

- [ ] TASK-08: Fix `test_download_image_sources` in `test_oe.py` — extract_sources no longer runs in `install()`
  - File: `odoo_env/test_oe.py`
  - REQ: REQ-08
  - Details:
    - Current `test_download_image_sources` (lines 351-386) calls `oe.install()` and asserts that an `extract_dist-packages.sh` command is found in the result
    - After TASK-07, that command is no longer present in `install()` output
    - Two options (choose one):
      a. **Delete the test entirely** — the old behavior it tested is now wrong by design
      b. **Redirect to `pull_images()`** — rewrite to call `oe.pull_images()` with `debug=True` and assert the same `extract_dist-packages.sh` command appears there
    - Preferred: option (b) — preserves coverage of `extract_sources` behavior, just moved to the correct command
    - Updated test skeleton:
      ```python
      def test_download_image_sources(self):
          self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
          self.mock_config_data.return_value["environment"] = "debug"
          options = MockArgs(
              debug=True, no_repos=False, nginx=False,
              extract_sources=True, client="test_client",
          )
          oe = OdooEnv(options)
          cmds = oe.pull_images()  # changed from oe.install()
          extract_cmd = next(
              (c for c in cmds if c._usr_msg and "Extracting dist-packages" in c._usr_msg),
              None,
          )
          self.assertIsNotNone(extract_cmd,
              "Expected Extracting dist-packages command in pull_images() debug mode")
          expected = [
              "docker", "run", "--rm", "-it",
              "--entrypoint", "/extract_dist-packages.sh",
              "-v", f"{OeConfig().base_dir}odoo-9.0/dist-packages/:/mnt/dist-packages:rw",
              "jobiols/odoo-jeo:9.0.debug",
          ]
          self.assertEqual(extract_cmd.command, expected)
      ```
    - Run full test suite — all tests MUST pass with 0 failures

---

## Final verification

- [ ] TASK-09: Run full test suite and confirm 0 failures
  - Command: `PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`
  - Expected: all tests in `test_oe.py`, `test_docker_client.py`, `test_image_manager.py`, `test_environment_manager.py` pass
  - Confirm the following specific tests are present and green:
    - `TestDockerClient.test_get_pull_command_returns_docker_pull_image`
    - `TestDockerClient.test_get_pull_command_does_not_contain_run`
    - `TestDockerClient.test_get_pull_command_has_no_flags`
    - `TestImageManager.test_pull_images_uses_pull_not_run`
    - `TestImageManager.test_pull_images_command_starts_with_docker_pull`
    - `TestImageManager.test_pull_images_calls_extract_sources_in_debug_mode`
    - `TestImageManager.test_pull_images_no_extract_sources_in_non_debug_mode`
    - `TestEnvironmentManager.test_install_never_calls_extract_sources`
    - `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_debug_mode`
    - `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_non_debug_mode`
    - `TestEnvironmentManager.test_install_does_not_reference_dist_dirs`

---

## Task summary

| Task | Type | File | REQ |
|------|------|------|-----|
| TASK-01 | Test | `test_docker_client.py` (new) | REQ-01, REQ-02, REQ-03 |
| TASK-02 | Impl | `services/docker_client.py` | REQ-01, REQ-02, REQ-03 |
| TASK-03 | Test | `test_image_manager.py` (new) | REQ-04, REQ-05, REQ-06, REQ-07 |
| TASK-04 | Impl | `managers/image_manager.py` | REQ-04, REQ-05 |
| TASK-05 | Fix test | `test_oe.py` | REQ-05 |
| TASK-06 | Test | `test_environment_manager.py` (new) | REQ-08, REQ-09, REQ-10, REQ-11 |
| TASK-07 | Impl | `managers/environment_manager.py` | REQ-08, REQ-09, REQ-10, REQ-11 |
| TASK-08 | Fix test | `test_oe.py` | REQ-08 |
| TASK-09 | Verify | all | all |

**Total tasks**: 9 (3 test-write, 3 implementation, 2 test-fix, 1 final verify)
**New test files**: 3
**Source files modified**: 3
**Strict TDD compliance**: tests written and confirmed failing before each implementation task
