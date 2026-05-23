# Proposal: install-from-url

## Intent

Fix the `oe -i` command so that:

1. **`oe -i` (no URL)**: Update repositories for the default/configured project — same as current expected behavior.
2. **`oe -i REPO_URL`**: Clone the repo from URL into a system temp directory, read its `__manifest__.py`, use the manifest to determine project configuration for a **first-time install only**, then discard the clone. This MUST NOT trigger for reinstallation of an existing project.

The critical bug is in `Client.get_manifest()` (line ~190 of `client.py`): when `-i` is passed **without** a URL, `self._args.install` is the boolean `True`. Since `True` is truthy, the code enters `self.get_manifest_from_url()`, which passes `True` as a URL to `git clone --depth 1 True tmpdir`, causing a crash.

## Scope

### In scope

- Fix the truthiness check in `Client.get_manifest()` so only a **string** URL triggers `get_manifest_from_url()`.
- Validate the URL argument before passing it to `git clone`.
- Ensure `client_path` is saved to `OeConfig` after a successful URL-based first install, so subsequent `-i` (no URL) calls find the project.
- Add unit tests covering the manifest resolution chain for both paths.

### Out of scope

- Changing the `-i` argparse interface (nargs, const, metavar).
- Adding support for `-i URL` on reinstallation / existing projects.
- Modifying the `EnvironmentManager.install()` flow itself.
- Memory/in-memory clone strategies — temp directory on disk is the chosen approach.

## Affected modules

| Module | Impact |
|---|---|
| `odoo_env/client.py` — `get_manifest()` | Bug fix: guard `get_manifest_from_url()` behind `isinstance(self._args.install, str)` check. |
| `odoo_env/client.py` — `get_manifest_from_url()` | Add input validation, error handling, and save `client_path` on success. |
| `odoo_env/oe.py` — `parse_args()` | No change required; argparse setup (`nargs="?"`, `const=True`) is correct. |
| `odoo_env/test_oe.py` | Add test cases for manifest resolution: URL path, no-URL path, nonexistent-client path. |

## Current behavior (bug)

```
oe -i                          # self._args.install = True (boolean)
 → get_manifest() sees truthy self._args.install
 → calls get_manifest_from_url()
 → git clone --depth 1 True /tmp/…
 → CRASH
```

## Proposed behavior

```
oe -i                          # self._args.install = True (boolean)
 → get_manifest() checks isinstance(self._args.install, str): False
 → skips get_manifest_from_url()
 → falls through to filesystem search (get_manifest_from_struct)
 → finds project via OeConfig client_path or CWD walk

oe -i git@github.com:org/repo.git  # self._args.install = "git@github.com:org/repo.git"
 → get_manifest() checks isinstance(self._args.install, str): True
 → calls get_manifest_from_url()
 → git clone --depth 1 git@github.com:org/repo.git /tmp/tmpXXXXXX
 → reads __manifest__.py from clone
 → OeConfig().save_client_path(name, path)
 → returns manifest, tempdir auto-cleaned
```

## Key design decisions

### Decision 1: Guard with `isinstance(…, str)` instead of `!= True`

`isinstance(self._args.install, str)` is explicit, Pythonic, and handles both the `True` case and any future non-string falsy/truthy values. An `!= True` check would pass for any other truthy value (e.g., a list, an int), which is fragile.

### Decision 2: Save client_path after URL-based install

`get_manifest_from_url()` currently returns the manifest but does NOT call `OeConfig().save_client_path()`. Without this, subsequent `oe -i` calls (no URL) will not find the project in `OeConfig.clients`, forcing a filesystem walk — and worse, may re-trigger the URL path if `install` is still set. Saving the path makes the second install a normal repo-update flow.

### Decision 3: Validate URL before git clone

`get_manifest_from_url()` MUST validate that `self._args.install` looks like a git URL before passing it to `subprocess.run`. A minimal check: ensure it's a non-empty string starting with `git@` or `https://`. If invalid, raise `OeError` with a clear message.

### Decision 4: Keep temp directory on disk (not in-memory)

The requirements specify clone to a system temp directory and discard after reading. `tempfile.TemporaryDirectory()` already provides this. No change needed to the cloning mechanism.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `client_path` save changes break existing config file format | Low | Medium | `save_client_path` already handles dedup; no format change. |
| URL validation rejects valid git URLs | Low | Low | Start with a permissive check (`git@` or `https://`); expand if needed. |
| First-time install with URL fails mid-way, leaving incomplete config | Medium | Medium | `save_client_path` is called only after successful manifest load. If git clone fails, `subprocess.run(check=True)` raises, nothing is saved. |
| Existing tests break due to `isinstance` change in `get_manifest()` | Low | Low | Existing tests mock `get_manifest` entirely; no impact expected. |

## Rollback plan

All changes are confined to `odoo_env/client.py` (`get_manifest()` guard, `get_manifest_from_url()` validation + save) and `odoo_env/test_oe.py` (new tests). Rollback is a simple `git revert` of the change commit. No database migrations, no config format changes. The `oe.py` argparse interface is untouched.

## Success criteria

1. `oe -i` (boolean) does NOT call `get_manifest_from_url()` — verified by unit test.
2. `oe -i git@github.com:org/repo.git` (string URL) clones, reads manifest, saves `client_path`, and discards tempdir — verified by unit test.
3. Invalid URL (e.g., `oe -i not-a-url`) produces a clear error message — verified by unit test.
4. All existing 32 tests continue to pass.
5. New tests bring manifest resolution chain coverage from 0 to meaningful coverage of both paths.

## RFC 2119 Keywords

- `get_manifest()` MUST check `isinstance(self._args.install, str)` before calling `get_manifest_from_url()`.
- `get_manifest_from_url()` MUST validate the URL argument before passing it to `git clone`.
- `get_manifest_from_url()` SHOULD save the resolved `client_path` via `OeConfig().save_client_path()` on success.
- The URL-based install path MUST only be triggered when `client_path` is not already configured (first install guard).
- The temp directory MUST be cleaned up after manifest loading (already handled by `TemporaryDirectory` context manager).
