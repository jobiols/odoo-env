# Spec: fix-install-pull-behavior

**Status**: draft
**Date**: 2026-04-12
**Change**: fix-install-pull-behavior

---

## 1. Requirements

### DockerClient

**REQ-01**
`DockerClient` SHALL expose a method `get_pull_command(image: str) -> list[str]`
that returns `["docker", "pull", image]`.

**REQ-02**
`DockerClient.get_pull_command` MUST NOT include the token `"run"` anywhere
in the returned list.

**REQ-03**
`DockerClient.get_pull_command` MUST NOT include any flags (e.g., `-d`, `--rm`,
`--entrypoint`) in the returned list — a plain pull with no options.

---

### ImageManager.pull_images()

**REQ-04**
`ImageManager.pull_images()` MUST call `DockerClient.get_pull_command` (not
`DockerClient.get_run_command`) to build the Docker command for each image.

**REQ-05**
`ImageManager.pull_images()` MUST return at least one `Command` whose
`.command` list starts with `["docker", "pull"]` for each image in the client.

**REQ-06**
When `OeConfig().debug` is `True`, `ImageManager.pull_images()` SHALL append
the commands produced by `extract_sources()` to its return value.

**REQ-07**
When `OeConfig().debug` is `False`, `ImageManager.pull_images()` MUST NOT
include any `rm -rf` or `mkdir` commands in its return value (i.e.,
`extract_sources()` output must be absent).

---

### EnvironmentManager.install()

**REQ-08**
`EnvironmentManager.install()` MUST NOT call `extract_sources()` or
`do_extract_sources()` under any condition, regardless of the value of
`OeConfig().debug`.

**REQ-09**
When `OeConfig().debug` is `True`, `EnvironmentManager.install()` MUST NOT
produce any command whose `.command` list contains the tokens `"rm"` and `"-rf"`
(i.e., no destructive removal of `dist-*` directories).

**REQ-10**
When `OeConfig().debug` is `False`, `EnvironmentManager.install()` MUST NOT
produce any command whose `.command` list contains `"rm"` with `-rf`
(same constraint, explicit for symmetry with REQ-09).

**REQ-11**
`EnvironmentManager.install()` SHALL remain idempotent: running it multiple
times MUST NOT destroy the contents of `dist-packages` or `dist-local-packages`
directories.

---

## 2. Acceptance Scenarios

### REQ-01 — get_pull_command returns correct command

```
Scenario: get_pull_command returns docker pull image
  Given a DockerClient instance
  When get_pull_command("postgres:17.5-alpine") is called
  Then the return value is exactly ["docker", "pull", "postgres:17.5-alpine"]
```

---

### REQ-02 — get_pull_command has no "run" token

```
Scenario: get_pull_command does not contain "run"
  Given a DockerClient instance
  When get_pull_command("postgres:17.5-alpine") is called
  Then the string "run" is not present in any element of the returned list
```

---

### REQ-03 — get_pull_command has no flags

```
Scenario: get_pull_command returns a plain three-element list
  Given a DockerClient instance
  When get_pull_command("some-image:tag") is called
  Then the returned list has exactly 3 elements: ["docker", "pull", "some-image:tag"]
```

---

### REQ-04 — pull_images() delegates to get_pull_command

```
Scenario: pull_images uses get_pull_command, not get_run_command
  Given an ImageManager with a mocked DockerClient
  And the client has at least one image
  When pull_images() is called
  Then DockerClient.get_pull_command is called at least once
  And DockerClient.get_run_command is NOT called for pulling images
```

---

### REQ-05 — pull_images() command list starts with docker pull

```
Scenario: pull_images commands start with docker pull
  Given an ImageManager configured with a client that has one image named "postgres:17.5-alpine"
  When pull_images() is called with debug=False
  Then the first Command in the result has .command == ["docker", "pull", "postgres:17.5-alpine"]
```

---

### REQ-06 — pull_images() appends extract_sources in debug mode

```
Scenario: pull_images appends extract_sources commands when debug is True
  Given an ImageManager with debug=True
  And the client has one or more packs (dist-packages, dist-local-packages)
  When pull_images() is called
  Then the returned list contains commands from extract_sources()
  And at least one command in the tail of the list contains "rm" (the removal step)
```

---

### REQ-07 — pull_images() omits extract_sources in non-debug mode

```
Scenario: pull_images does not append extract_sources commands when debug is False
  Given an ImageManager with debug=False
  When pull_images() is called
  Then no command in the returned list has a .command that contains "rm" with "-rf"
  And no command in the returned list has a .command that starts with ["mkdir"]
  (i.e., no extract_sources output is present)
```

---

### REQ-08 — install() never calls extract_sources

```
Scenario: install never delegates to extract_sources or do_extract_sources
  Given an EnvironmentManager with debug=True
  And a mock on OdooEnv.do_extract_sources
  When install() is called
  Then do_extract_sources is never called
```

---

### REQ-09 — install() produces no rm -rf in debug mode

```
Scenario: install in debug mode produces no destructive removal commands
  Given an OdooEnv configured with debug=True
  When oe.install() is called
  Then no Command in the returned list has both "rm" and "-rf" in its .command list
```

---

### REQ-10 — install() produces no rm -rf in non-debug mode

```
Scenario: install in non-debug mode produces no destructive removal commands
  Given an OdooEnv configured with debug=False
  When oe.install() is called
  Then no Command in the returned list has both "rm" and "-rf" in its .command list
```

---

### REQ-11 — install() is idempotent regarding dist-* directories

```
Scenario: install does not touch dist-packages or dist-local-packages directories
  Given an OdooEnv configured with debug=True
  When oe.install() is called
  Then no Command in the returned list references "dist-packages"
  And no Command in the returned list references "dist-local-packages"
```

---

## 3. Test Mapping

| Scenario | Test File | Test Method |
|----------|-----------|-------------|
| REQ-01: get_pull_command returns docker pull image | `odoo_env/test_docker_client.py` | `TestDockerClient.test_get_pull_command_returns_docker_pull_image` |
| REQ-02: get_pull_command does not contain "run" | `odoo_env/test_docker_client.py` | `TestDockerClient.test_get_pull_command_does_not_contain_run` |
| REQ-03: get_pull_command returns plain three-element list | `odoo_env/test_docker_client.py` | `TestDockerClient.test_get_pull_command_has_no_flags` |
| REQ-04: pull_images uses get_pull_command not get_run_command | `odoo_env/test_image_manager.py` | `TestImageManager.test_pull_images_uses_pull_not_run` |
| REQ-05: pull_images commands start with docker pull | `odoo_env/test_image_manager.py` | `TestImageManager.test_pull_images_command_starts_with_docker_pull` |
| REQ-06: pull_images appends extract_sources in debug mode | `odoo_env/test_image_manager.py` | `TestImageManager.test_pull_images_calls_extract_sources_in_debug_mode` |
| REQ-07: pull_images omits extract_sources in non-debug mode | `odoo_env/test_image_manager.py` | `TestImageManager.test_pull_images_no_extract_sources_in_non_debug_mode` |
| REQ-08: install never calls extract_sources | `odoo_env/test_environment_manager.py` | `TestEnvironmentManager.test_install_never_calls_extract_sources` |
| REQ-09: install in debug mode produces no rm -rf | `odoo_env/test_environment_manager.py` | `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_debug_mode` |
| REQ-10: install in non-debug mode produces no rm -rf | `odoo_env/test_environment_manager.py` | `TestEnvironmentManager.test_install_does_not_call_extract_sources_in_non_debug_mode` |
| REQ-11: install does not touch dist-* dirs | `odoo_env/test_environment_manager.py` | `TestEnvironmentManager.test_install_does_not_reference_dist_dirs` |

---

## Implementation Notes (for test authors)

### Test isolation pattern (from `test_oe.py`)

Every test class `setUp` MUST:

1. Reset `OeConfig` singleton:
   ```python
   if OeConfig in SingletonMeta._instances:
       del SingletonMeta._instances[OeConfig]
   ```

2. Patch `OeConfig._get_config_data` to return a config dict.

3. Patch `OeConfig._save_config_data` to prevent writes.

4. Patch `odoo_env.client.Client.get_manifest` with the relevant test manifest.

5. Call all patchers `.start()` and stop them in `tearDown`.

### MockArgs pattern

Reuse the existing `MockArgs` class from `test_oe.py` or duplicate it in each
new test file. All known args must have defaults; tests only override the ones
they care about.

### DockerClient tests (REQ-01 to REQ-03)

`DockerClient` is a pure value object with no dependencies — tests instantiate
it directly without any mocking.

### ImageManager tests (REQ-04 to REQ-07)

`ImageManager.__init__` calls `OeConfig().get_client()` and `Client(...)`.
Tests must:

- Apply the full `OeConfig` mock chain from above.
- Either inject a mock `DockerClient` or patch
  `odoo_env.services.docker_client.DockerClient.get_pull_command` /
  `get_run_command` at the method level.
- For REQ-04, use `unittest.mock.patch` on both `get_pull_command` and
  `get_run_command` to assert call counts.

### EnvironmentManager tests (REQ-08 to REQ-11)

The simplest approach is to go through `OdooEnv` (same as existing `test_install`
in `test_oe.py`) with `debug=True` or `debug=False` and inspect the full
`Command` list. For REQ-08, additionally patch `OdooEnv.do_extract_sources`
and assert it was never called (`assert_not_called`).
