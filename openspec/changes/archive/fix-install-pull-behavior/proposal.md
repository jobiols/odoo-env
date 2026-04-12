# Proposal: fix-install-pull-behavior

**Status**: draft  
**Date**: 2026-04-12  

---

## Intent

Two commands are doing work that belongs to the other:

1. `oe -i` (install) silently destroys and recreates `dist-packages` and `dist-local-packages` when `OeConfig().debug` is True. Install should be idempotent and limited to directory scaffolding + source repo cloning/updating. It must NEVER touch the dist-* directories.

2. `oe -p` (pull) calls `docker run <image>` instead of `docker pull <image>`. This starts a container rather than pulling the image from the registry. Additionally, `extract_sources()` (which performs the destructive rm -rf + recreate of dist-* dirs) belongs here in debug mode, not in install.

The result is that the user cannot safely re-run `oe -i` (it wipes debuggable Python packages), and `oe -p` never actually updates images from the Docker registry.

---

## Scope

### Files that will change

| File | What changes |
|------|-------------|
| `odoo_env/services/docker_client.py` | Add `get_pull_command(image: str) -> list[str]` |
| `odoo_env/managers/image_manager.py` | `pull_images()`: replace `get_run_command` with `get_pull_command`; keep `extract_sources()` call in debug mode |
| `odoo_env/managers/environment_manager.py` | `install()`: remove the `if OeConfig().debug: ... do_extract_sources(...)` block entirely |

### Behaviors that change

| Command | Before | After |
|---------|--------|-------|
| `oe -i` | mkdir + clone/update repos + (debug) rm -rf dist-* + extract | mkdir + clone/update repos only |
| `oe -p` | `docker run <image>` (starts container) + (debug) extract_sources | `docker pull <image>` for each image + (debug) extract_sources |

### What does NOT change

- `extract_sources()` implementation itself — logic is correct, just in the wrong place
- `do_extract_sources()` on `OdooEnv` — still delegates to `ImageManager.extract_sources()`
- All other manager methods (run, stop, update, qa, etc.)
- The command pattern: all methods continue to return `list[Command]`, never executing directly

---

## Approach

### Step 1 — Add `get_pull_command` to `DockerClient`

```python
def get_pull_command(self, image: str) -> list[str]:
    return ["docker", "pull", image]
```

Signature follows the same convention as `get_stop_command` and `get_rm_command`: takes a string, returns a `list[str]`. No flags needed for a basic pull.

### Step 2 — Fix `ImageManager.pull_images()`

Replace:
```python
cmd_list = self.docker_client.get_run_command(image.name)
```
With:
```python
cmd_list = self.docker_client.get_pull_command(image.name)
```

The `extract_sources()` call in debug mode remains untouched — it belongs here.

### Step 3 — Fix `EnvironmentManager.install()`

Remove lines 101-103 entirely:
```python
# DELETE THIS BLOCK:
if OeConfig().debug:
    ret.extend(self.parent.do_extract_sources(self._client.name))
```

No replacement needed. `install()` ends after `_process_repos()`.

### Tests to write (Strict TDD — write tests FIRST)

All tests go under `odoo_env/` following the existing `test_*.py` pattern.

1. `test_docker_client.py` (new or extend existing):
   - `test_get_pull_command_returns_docker_pull_image` — asserts `["docker", "pull", "postgres:17.5-alpine"]`
   - `test_get_pull_command_does_not_contain_run` — asserts `"run"` not in result

2. `test_image_manager.py` (new or extend existing):
   - `test_pull_images_uses_pull_not_run` — mock `DockerClient.get_pull_command`, assert it is called (not `get_run_command`)
   - `test_pull_images_calls_extract_sources_in_debug_mode` — with `debug=True`, assert `extract_sources` commands are appended
   - `test_pull_images_no_extract_sources_in_non_debug_mode` — with `debug=False`, assert no rm/mkdir commands present

3. `test_environment_manager.py` (new or extend existing):
   - `test_install_does_not_call_extract_sources_in_debug_mode` — with `debug=True`, assert no rm/mkdir for dist-* dirs in the returned command list
   - `test_install_does_not_call_extract_sources_in_non_debug_mode` — same assertion for `debug=False`

---

## Risks

### Regression: users who relied on `oe -i` running extract_sources in debug mode

Existing debug workflows may have been using `oe -i` to re-extract Python packages. After this change, they must use `oe -p` instead. This is a behavioral change but it is the CORRECT behavior — document in commit message.

### `get_pull_command` — no flags

A plain `docker pull <image>` is sufficient for registry pulls. If the image tag is `latest`, Docker always fetches the newest digest. No platform flag is added now; can be extended later if multi-arch pulls are needed (out of scope).

### `extract_sources` still uses `get_run_command` internally

`extract_sources()` calls `docker run ... --entrypoint=/extract_{module}.sh` which is correct — it runs a container with a custom entrypoint to copy files out. This is NOT a pull; it is intentional usage of `get_run_command`. No change needed there.

### Test isolation for `ImageManager`

`ImageManager.__init__` calls `OeConfig().get_client()` and `Client(...)`, which may require a config fixture. Tests must mock `OeConfig` and `Client` or use an existing test fixture pattern from the project.

---

## Out of Scope

- Refactoring `extract_sources()` internals
- Adding `--platform` support to `get_pull_command`
- Changing how `oe -i` handles the nginx block or chown/chmod commands
- Any changes to `run_environment`, `stop_environment`, `run_client`, `update`, or `qa`
- Changing the CLI argument parsing or `OdooEnv.build_commands()` dispatch logic
- CI/CD pipeline changes
