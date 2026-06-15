# Tasks: install-by-client-name

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~230 (~150 tests, ~80 prod across 3 files) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |

Decision needed before apply: No

---

## Overview

Add client-name resolution to `oe -i`. Strict TDD is active: tests MUST fail (RED)
before implementation (GREEN). Phases: Infrastructure → RED → GREEN → VERIFY.

Test runner:
`PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`

Spec coverage: REQ-INSTALL-002 (new scenario), 003 (modified), 008, 009, 010.

---

## Phase 1: Infrastructure

### Task 1.1 — Add `org` to MockArgs defaults

- File: `odoo_env/test_helpers.py`
- In `MockArgs.__init__` defaults dict, add `"org": None`.
- Rationale: new argparse dest `org`; test args must default it so existing
  `MockArgs(...)` constructions keep working.

---

## Phase 2: RED — failing tests first

### Task 2.1 — Org config tests (REQ-INSTALL-009)

- File: `odoo_env/test_config.py` (new)
- Add `TestOrganizationConfig(unittest.TestCase)` mirroring the patching style of
  `test_client.py` (`OeConfig.reset()`, patch `_get_config_data` / `_save_config_data`).
- Tests:
  - `test_org_default_when_missing_persists`: config without `organization` →
    `OeConfig().get_organization()` returns `"quilsoft-org"` AND `_save_config_data`
    was called (default persisted).
  - `test_org_read_from_config`: config has `organization: acme-org` →
    `get_organization()` returns `"acme-org"` and does NOT persist again.
  - `test_save_organization_persists`: `save_organization("acme-org")` sets the key
    and calls `_save_config_data`.
  - `test_save_organization_noop_when_unchanged`: saving the same value does NOT
    call `_save_config_data` (mirror `save_base_dir`).
  - `test_persist_config_saves_org_flag`: `OeConfig(MockArgs(org="acme-org"))` +
    `persist_config()` persists `organization: acme-org`.

### Task 2.2 — Canonical URL builder + name validation/normalize tests (REQ-INSTALL-008/010)

- File: `odoo_env/test_client.py`
- Add `TestBuildRepoUrl(unittest.TestCase)` (own setUp patching `OeConfig`).
- Tests:
  - `test_build_url_default_org`: client `"labutic"`, org default →
    `"git@github.com:quilsoft-org/cl-labutic.git"`.
  - `test_build_url_configured_org`: org `"acme-org"` →
    `"git@github.com:acme-org/cl-labutic.git"`.
  - `test_build_url_lowercases_name`: `"Labutic"` → `...cl-labutic.git`.
  - `test_build_url_rejects_space`: `"foo bar"` → raises `OeError`.
  - `test_build_url_rejects_slash`: `"foo/bar"` → raises `OeError`.
  - `test_build_url_rejects_empty`: `""` → raises `OeError`.

### Task 2.3 — Resolution tests in get_manifest_from_url (REQ-INSTALL-003)

- File: `odoo_env/test_client.py` (extend `TestGetManifest`)
- Add tests:
  - `test_full_git_url_used_verbatim`: install `"git@github.com:org/repo.git"` →
    clone arg `call_args[4] == "git@github.com:org/repo.git"`.
  - `test_full_https_url_used_verbatim`: install `"https://github.com/org/repo.git"`
    → verbatim clone arg.
  - `test_client_name_builds_canonical_url`: install `"labutic"`, default org →
    clone arg `== "git@github.com:quilsoft-org/cl-labutic.git"`.
  - `test_empty_install_raises`: install `""` → `get_manifest_from_url()` raises
    `OeError`.

### Task 2.4 — Revise existing tests that assumed any non-URL is invalid

- File: `odoo_env/test_client.py`
- `test_invalid_url_raises_oe_error` (install `"not-a-url"`): REPLACE expectation.
  `"not-a-url"` is now a valid client name → assert it builds
  `"git@github.com:quilsoft-org/cl-not-a-url.git"` (clone arg) instead of raising.
  Rename to `test_non_url_string_builds_canonical_url`.
- `test_empty_url_raises_oe_error` (install `""`): KEEP — empty still raises `OeError`.
- Update module docstring to mention REQ-INSTALL-008/009/010.

### Task 2.5 — argparse `--org` + `-i` metavar tests (REQ-INSTALL-009)

- File: `odoo_env/test_oe.py`
- Add tests (parse via `oe.parse_args` with patched `sys.argv` or call the parser):
  - `test_org_flag_parsed`: `oe --org acme-org` → `args.org == "acme-org"`.
  - `test_install_metavar_is_client`: assert the `-i` action `metavar == "CLIENT"`.
  - `test_org_only_persists_and_returns`: invoking `main()`/guard with only `--org`
    set persists organization and returns without building commands (mirror the
    existing `--base-dir` standalone-guard test if present; otherwise assert
    `save_organization` called and no `OdooEnv.build_commands`).

### Task 2.6 — Run tests, confirm RED

- Run the suite; the new tests in 2.1–2.5 MUST fail (functions/keys not implemented yet).

---

## Phase 3: GREEN — implementation

### Task 3.1 — Config: organization support

- File: `odoo_env/config.py`
- Add `get_organization()`:
  - read `organization` from `_config_data`;
  - if missing, set `_config_data["organization"] = "quilsoft-org"`, call
    `_save_config_data()`, and return `"quilsoft-org"`;
  - else return the stored value.
- Add `save_organization(value)`: no-op if unchanged; else set key + `_save_config_data()`.
- In `persist_config()`: `if self._args.org: self.save_organization(self._args.org)`.
- Optional convenience: `@property organization` returning `get_organization()`.

### Task 3.2 — oe.py: argparse changes

- File: `odoo_env/oe.py`
- `-i` argument: change `metavar="REPO_URL"` → `metavar="CLIENT"`; rewrite help to:
  install/update environment; with no value repos come from the manifest; with a
  CLIENT name it builds `git@github.com:<org>/cl-<client>.git`; a full git URL is also
  accepted.
- Add `--org` argument: `dest="org"`, `help="Set the GitHub organization used to build
  canonical repo URLs (e.g. quilsoft-org). Persistent."`.
- In `main()`, add `args.org` handling to the standalone-persist guard alongside
  `args.base_dir` so `oe --org X` (no action flag) persists and returns. Include
  `args.org` is NOT an action; extend the `any([...])` action list check so a lone
  `--org` returns early after `persist_config()`.

### Task 3.3 — client.py: URL resolution + builder

- File: `odoo_env/client.py`
- Add static `_is_full_git_url(value: str) -> bool`: `value.startswith(("git@",
  "https://"))`.
- Add `build_repo_url(client_name: str) -> str`:
  - validate: non-empty, no space, no `/` → else `msg.err(...)` (raises `OeError`);
  - `name = client_name.strip().lower()`;
  - `org = OeConfig().get_organization()`;
  - return `f"git@github.com:{org}/cl-{name}.git"`.
- Add `_resolve_install_url(value: str) -> str`: return `value` if
  `_is_full_git_url(value)` else `build_repo_url(value)`.
- In `__init__` (the `elif isinstance(self._args.install, str)` branch): resolve
  `url = self._resolve_install_url(self._args.install)` and pass `url` to
  `_discover_from_url(url)`.
- In `get_manifest_from_url()`: compute
  `url = self._resolve_install_url(self._args.install)` when install is a non-empty
  string; keep the final guard that the resolved `url` starts with `git@`/`https://`
  and raise `OeError` otherwise (covers empty string → `build_repo_url("")` raises).

### Task 3.4 — Run tests, confirm GREEN

- Run full suite; all new + existing tests pass.

---

## Phase 4: VERIFY

### Task 4.1 — Full suite + regression

- Run: `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`
- Zero failures, zero regressions.

### Task 4.2 — Spec scenario cross-check

- Map each REQ-INSTALL-002 (new), 003, 008, 009, 010 scenario to a passing test.

### Task 4.3 — Manual smoke (optional, no network)

- Confirm `oe -i --help` shows `-i [CLIENT]` and `--org` appears in help.
- Confirm `oe --org acme-org` persists and returns (dry, with config mocked or a temp
  HOME) — optional if covered by unit tests.
