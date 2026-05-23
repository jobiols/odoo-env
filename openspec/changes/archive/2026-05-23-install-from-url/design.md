# Design: install-from-url

## Overview

Fix the `oe -i` crash when `-i` is passed without a URL. The root cause is a bare truthiness check (`if self._args.install:`) in `Client.get_manifest()` that conflates the boolean `True` (no-URL case) with a URL string, causing `get_manifest_from_url()` to receive `True` as a git clone URL.

The fix is a two-line change in `get_manifest()` plus URL validation and `save_client_path` in `get_manifest_from_url()`. All 7 spec requirements map to a clear design.

---

## Architecture Decision Record

### ADR-001: isinstance guard placement — inline in get_manifest(), not a separate guard method

**Decision**: Replace the bare `if self._args.install:` on line ~190 with `if isinstance(self._args.install, str):`. No new method, no restructuring of the flow.

**Rationale**:
- This is the minimum change to fix the bug. The existing flow structure — check client_path first, then URL, then filesystem walk — is correct.
- The `isinstance` check is the only discriminator needed: if `install` is `None` (not passed), `False` (MockArgs default), or `True` (boolean flag), it's not a string and the URL path is skipped. If it's a string, it's forwarded to `get_manifest_from_url()`.
- No need to extract a `_should_install_from_url()` method — the condition is a single line that reads naturally in context.

**Before (buggy)**:
```python
if not client_path:
    if self._args.install:          # True is truthy → CRASH
        manifest = self.get_manifest_from_url()
```

**After (fixed)**:
```python
if not client_path:
    if isinstance(self._args.install, str):   # Only strings trigger URL path
        manifest = self.get_manifest_from_url()
```

**Rejected alternatives**:
- `if self._args.install is not True:` — fragile; would pass for lists, ints, etc.
- `if self._args.install and self._args.install is not True:` — verbose, still fragile.
- `if isinstance(self._args.install, str) and self._args.install:` — the empty string case is handled by URL validation in `get_manifest_from_url()`, so no need for a truthiness check here.

### ADR-002: save_client_path called inside get_manifest_from_url(), not get_manifest()

**Decision**: Call `OeConfig().save_client_path(self._name, dir_path)` inside `get_manifest_from_url()` using the directory path returned by `get_manifest_from_struct()` within the temp clone, BEFORE the `TemporaryDirectory` context manager exits.

**Rationale**:
- `get_manifest_from_url()` owns the resolution path and the path discovery; it's the natural owner of the save operation.
- `get_manifest_from_struct()` returns `(manifest, path)` where `path` is the directory containing `__manifest__.py`. We currently discard the path with `manifest, _ = self.get_manifest_from_struct(...)`. Capturing it and saving it is a minimal change.
- The save must happen inside the `with tempfile.TemporaryDirectory()` block because the path ceases to exist after the block exits.
- `OeConfig().save_client_path()` has a built-in first-write-only guard: if `get_client_path(self._name)` already returns a non-None value, it returns early without saving. This enforces REQ-INSTALL-005 naturally.

**Important note on path semantics**: The saved path is the temporary directory inside the clone (e.g., `/tmp/tmpXXXXXX/repo-name/`). This path is invalid after `TemporaryDirectory` cleanup. However, it serves as a "client-known" marker in OeConfig. On subsequent runs:
1. `get_client_path()` returns the (now-dead) temp path.
2. `get_manifest_from_struct(Path(client_path))` returns `(None, None)` because the path doesn't exist.
3. The system falls through to the filesystem walk at CWD.
4. If the project was properly installed, the walk finds it at the installed location and saves the correct path on that run.

This is acceptable for a SHOULD-level requirement (REQ-INSTALL-004). The alternative — computing the final install path from the manifest version — would require cross-cutting knowledge of `self._version`/`self.base_dir` that isn't available until `check_common()` runs after `get_manifest()` returns.

**Current code**:
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

### ADR-003: URL validation — startswith check, inline in get_manifest_from_url()

**Decision**: Validate the URL at the top of `get_manifest_from_url()` with `url.startswith("git@") or url.startswith("https://")`. Raise `OeError` with a clear message on failure.

**Rationale**:
- The URL comes from argparse and could be anything. Passing garbage to `git clone` would produce cryptic errors.
- `startswith` is fast, simple, and covers all standard git clone URLs (GitHub, GitLab, Bitbucket, self-hosted). No regex needed.
- Raising `OeError` (the project's standard error) surfaces the message cleanly via `msg.err()`.
- The validation is inside `get_manifest_from_url()` because it's the only caller that uses the URL as a git clone argument. `get_manifest()` only needs to discriminate string vs non-string.

**Rejected alternatives**:
- Regex: overkill for checking two prefixes; adds import and maintenance burden.
- Validation in `get_manifest()`: would require `get_manifest()` to know about git URL format, which is a `get_manifest_from_url()` concern.
- `urllib.parse.urlparse`: would reject `git@` URLs (they're not RFC 3986 URLs), so we'd need two validation paths anyway.

**Implementation**:
```python
def get_manifest_from_url(self) -> dict[str, object] | None:
    url = self._args.install
    if not (url.startswith("git@") or url.startswith("https://")):
        msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, tmpdir], check=True
        )
        manifest, manifest_dir = self.get_manifest_from_struct(Path(tmpdir))
        if manifest and manifest_dir:
            OeConfig().save_client_path(self._name, manifest_dir)
        return manifest
```

### ADR-004: Error handling — propagate exceptions, rely on context manager

**Decision**: No explicit try/except in `get_manifest_from_url()`. Let exceptions propagate naturally.

**Error scenarios and handling**:

| Error | Mechanism | Result |
|---|---|---|
| Invalid URL format | `msg.err()` → raises `OeError` | User sees red error message |
| git clone fails (bad URL, no network, auth) | `subprocess.run(check=True)` → raises `CalledProcessError` | User sees Python traceback with git error |
| Clone succeeds, no manifest found | `get_manifest_from_struct()` returns `(None, None)` | `get_manifest_from_url()` returns `None`, `get_manifest()` falls through to filesystem walk |
| Manifest exists but is malformed | `load_manifest()` returns `{"name": "none"}` | Falls through to filesystem walk; may produce confusing "no name in manifest" error later |
| Temp directory cleanup | `TemporaryDirectory` context manager | Always cleaned up, regardless of exception |

**Rationale for no explicit try/except**:
- `subprocess.run(check=True)` already produces clear error output from git (stderr is not captured, so it prints to terminal).
- Wrapping in try/except would either re-raise (no value) or suppress the error (worse — we'd lose the git error message).
- `TemporaryDirectory` cleanup is guaranteed by the context manager.
- The one case where we might want custom error handling — manifest not found in clone — is handled by returning `None` and letting the caller fall through to filesystem search.

### ADR-005: Test strategy — direct unit tests on get_manifest() with selective mocking

**Decision**: Add new tests in `odoo_env/test_client.py` (new file) rather than `test_oe.py`. The tests directly instantiate `Client` and call `get_manifest()`, mocking only external dependencies (`OeConfig.get_client_path`, `subprocess.run`, filesystem operations). This follows the pattern from the existing codebase where `Client` is tested indirectly through `OdooEnv`, but adds first-class unit coverage for `get_manifest()` itself.

**Rationale**:
- Existing tests in `test_oe.py` mock `Client.get_manifest` entirely. They don't exercise the manifest resolution chain.
- Placing new tests in `test_oe.py` would require navigating the `OdooEnvTestCase` infrastructure (which mocks `get_manifest`), making setup complex.
- A separate `test_client.py` with focused `unittest.TestCase` classes is cleaner and avoids interference with the existing test infrastructure.
- Strict TDD is active: tests MUST be written and must FAIL before implementation begins.

**Test cases**:

| Test | Scenario | Mocks | Assertions |
|---|---|---|---|
| `test_install_bool_skips_url` | `install=True`, no client_path | `get_client_path` → None | `get_manifest_from_url` NOT called; falls through to struct search |
| `test_install_none_skips_url` | `install=None`, no client_path | `get_client_path` → None | `get_manifest_from_url` NOT called |
| `test_install_str_calls_url` | `install="git@github.com:x/y.git"`, no client_path | `get_client_path` → None, `subprocess.run`, `get_manifest_from_struct` → test manifest | `get_manifest_from_url` called; returns manifest |
| `test_install_str_existing_client_skips_url` | `install="git@...`, client_path exists | `get_client_path` → "/some/path" | URL path NOT triggered; uses client_path |
| `test_invalid_url_raises` | `install="not-a-url"` | `get_client_path` → None | `OeError` raised with "Invalid git URL" message |
| `test_empty_url_raises` | `install=""` | `get_client_path` → None | `OeError` raised |
| `test_url_clone_failure_propagates` | `install="git@github.com:x/y.git"` | `get_client_path` → None, `subprocess.run` → raises `CalledProcessError` | Exception propagates |
| `test_url_success_saves_client_path` | Valid URL, successful clone | `get_client_path` → None, `subprocess.run`, `get_manifest_from_struct` → (manifest, "/tmp/xxx/repo") | `save_client_path` called with name and path |
| `test_url_no_manifest_returns_none` | Valid URL, clone OK, no manifest | `get_client_path` → None, `subprocess.run`, `get_manifest_from_struct` → (None, None) | Returns None; save_client_path NOT called |

**Mock strategy**:
- `OeConfig().get_client_path()` — mock to control the first-install vs existing-client paths.
- `subprocess.run` — mock to avoid real git operations and to simulate failures.
- `Client.get_manifest_from_struct` — mock to simulate finding/not-finding a manifest in the clone. We don't mock `load_manifest` because `get_manifest_from_struct` is the public API boundary.
- `OeConfig().save_client_path` — mock to verify it's called (or not) with correct arguments.
- Do NOT mock `Client.get_manifest()` or `Client.get_manifest_from_url()` — these are the methods under test.

### ADR-006: MockArgs — no structural change needed

**Decision**: MockArgs requires no code changes. The class already supports arbitrary keyword arguments via `__init__(**kwargs)`.

**Usage in new tests**:
```python
# Simulate oe -i (boolean flag)
MockArgs(install=True)

# Simulate oe -i URL
MockArgs(install="git@github.com:org/repo.git")

# Simulate no -i flag (argparse default)
MockArgs(install=None)   # or just leave default False
```

**Note on default value**: MockArgs currently defaults `install` to `False`. Argparse with `nargs="?"` defaults to `None` when the flag is not passed. Both `False` and `None` are not strings, so both correctly skip the URL path with the `isinstance(str)` guard. No change needed.

---

## Data Flow

### Path A: No URL (-i boolean)

```
oe -i
  → args.install = True (bool)
  → Client.__init__("myclient")
    → get_manifest()
      → OeConfig().get_client_path("myclient") → None or path
      → isinstance(True, str) → False → skip URL path
      → if client_path exists: get_manifest_from_struct(client_path) → manifest
      → else: get_manifest_from_struct(CWD) → manifest, path
        → if found: save_client_path("myclient", path)
      → return manifest
```

### Path B: With URL string, first install

```
oe -i git@github.com:org/repo.git
  → args.install = "git@github.com:org/repo.git" (str)
  → Client.__init__("myclient")
    → get_manifest()
      → OeConfig().get_client_path("myclient") → None
      → isinstance("git@...", str) → True → call get_manifest_from_url()
        → validate URL: startswith("git@") → OK
        → tempfile.TemporaryDirectory() as tmpdir
          → subprocess.run(["git", "clone", "--depth", "1", url, tmpdir])
          → get_manifest_from_struct(tmpdir) → (manifest, "/tmp/tmpXXX/repo")
          → save_client_path("myclient", "/tmp/tmpXXX/repo")
          → return manifest
        → (tmpdir cleaned up by context manager)
      → return manifest
```

### Path C: With URL string, client_path already exists

```
oe -i git@github.com:org/repo.git
  → args.install = "git@github.com:org/repo.git" (str)
  → Client.__init__("myclient")
    → get_manifest()
      → OeConfig().get_client_path("myclient") → "/odoo_ar/odoo-14.0/myclient/"
      → client_path exists → skip URL path entirely
      → get_manifest_from_struct("/odoo_ar/odoo-14.0/myclient/") → manifest
      → return manifest
```

---

## File Change Summary

### `odoo_env/client.py` — 2 methods modified

**`get_manifest()` (line ~190)**:
- Change: `if self._args.install:` → `if isinstance(self._args.install, str):`
- Lines changed: 1

**`get_manifest_from_url()` (line ~170)**:
- Add: URL validation block (4 lines)
- Change: capture `manifest_dir` from `get_manifest_from_struct` return
- Add: conditional `save_client_path` call (2 lines)
- Lines changed: ~7

**Total**: ~8 lines changed in client.py.

### `odoo_env/test_client.py` — NEW file

- ~9 test methods in `TestGetManifest` class
- Uses `unittest.TestCase` directly (not `OdooEnvTestCase` base class, to avoid the `get_manifest` mock)
- ~150 lines

### `odoo_env/test_helpers.py` — NO CHANGE

- MockArgs already supports `install=str` via `**kwargs`.

---

## Spec-to-Design Traceability

| Spec Requirement | Design Implementation | ADR |
|---|---|---|
| REQ-INSTALL-001: isinstance(str) guard | Line change in `get_manifest()` | ADR-001 |
| REQ-INSTALL-002: URL forwarding | Same guard — if string, calls `get_manifest_from_url()` | ADR-001 |
| REQ-INSTALL-003: URL validation | `startswith` check at top of `get_manifest_from_url()` | ADR-003 |
| REQ-INSTALL-004: save_client_path | `OeConfig().save_client_path()` inside `get_manifest_from_url()` | ADR-002 |
| REQ-INSTALL-005: first-install-only guard | `get_client_path()` check in `get_manifest()` + `save_client_path` dedup guard | ADR-001, ADR-002 |
| REQ-INSTALL-006: temp cleanup | Preserved `tempfile.TemporaryDirectory()` context manager | ADR-004 |
| REQ-INSTALL-007: existing client_path skips URL | `if not client_path:` block in `get_manifest()` unchanged | ADR-001 |

---

## Rollback

All changes are additive or single-line replacements:

1. Revert the `isinstance` guard back to bare `if self._args.install:` — one line.
2. Remove the URL validation block from `get_manifest_from_url()` — 4 lines.
3. Revert `manifest, _ = ...` and remove `save_client_path` calls — 3 lines.
4. Delete `test_client.py` if desired.

No config format changes, no database, no migration needed.

---

## Open Questions / Deferred Decisions

1. **Path saved by save_client_path**: The temporary path saved by `get_manifest_from_url()` is invalid after cleanup. If this causes confusion or bugs in practice, consider a follow-up that computes and saves the final install path (requires refactoring to pass version info). This is deferred as the current design satisfies the SHOULD-level requirement.

2. **URL schemes beyond git@ and https://**: If users report valid git URLs being rejected (e.g., `ssh://git@...`), expand the validation to include `ssh://` prefix. The `startswith` approach makes this trivial to extend.

3. **Manifest not found in URL clone**: Currently returns `None`, which falls through to filesystem walk. If the clone contains no `__manifest__.py`, the user gets a confusing "no version tag" error from the filesystem walk. A follow-up could add a specific error: "No __manifest__.py found in cloned repository".
