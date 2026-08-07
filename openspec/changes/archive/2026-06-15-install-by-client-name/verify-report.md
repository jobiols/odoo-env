# Verify Report: install-by-client-name

## Result: ✅ PASS

## Test run

Command:
`PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`

- Ran **208 tests** — `OK` (0 failures, 0 errors).
- Strict TDD honored: new tests failed first (RED: 2 failures + 13 errors), then
  passed after implementation (GREEN).
- LSP/Pyright: 0 errors on `oe.py`, `config.py`, `client.py`, `test_*.py`.

## New tests (14)

- `test_config.TestOrganizationConfig` (5): default+persist, read-from-config,
  save persists, save no-op, persist_config saves `--org`.
- `test_client.TestBuildRepoUrl` (6): default org, configured org, lowercase,
  reject space / slash / empty.
- `test_oe.TestParseArgs` (3): `--org` parsed, `-i <name>` parsed, help shows
  `[CLIENT]` + `--org` and no longer `REPO_URL`.
- `test_client.TestGetManifest` extended: full git@/https URLs verbatim, bare
  name → canonical URL, non-URL string → canonical, empty → `OeError`.

## Spec scenario cross-check

| Requirement | Scenario | Test |
|---|---|---|
| REQ-INSTALL-002 | bare client name | `test_client_name_builds_canonical_url` |
| REQ-INSTALL-003 | https verbatim | `test_full_https_url_used_verbatim` |
| REQ-INSTALL-003 | git@ verbatim | `test_full_git_url_used_verbatim` |
| REQ-INSTALL-003 | name → canonical | `test_client_name_builds_canonical_url` |
| REQ-INSTALL-003 | empty → error | `test_empty_install_raises` |
| REQ-INSTALL-008 | default org URL | `test_build_url_default_org` |
| REQ-INSTALL-008 | configured org URL | `test_build_url_configured_org` |
| REQ-INSTALL-009 | --org persisted | `test_org_flag_parsed` / `test_persist_config_saves_org_flag` |
| REQ-INSTALL-009 | read from config | `test_org_read_from_config` |
| REQ-INSTALL-009 | default + persist | `test_org_default_when_missing_persists` |
| REQ-INSTALL-010 | lowercase | `test_build_url_lowercases_name` |
| REQ-INSTALL-010 | reject space | `test_build_url_rejects_space` |
| REQ-INSTALL-010 | reject slash | `test_build_url_rejects_slash` |

## Manual smoke

- `oe -i Labutic` → `args.install == "Labutic"` (resolution/lowercasing happens
  downstream in `build_repo_url`).
- `oe -h` shows `-i [CLIENT]` and `--org ORG`; `REPO_URL` removed.

## Files changed

- `odoo_env/config.py` — `get_organization()`, `save_organization()`, persist `--org`.
- `odoo_env/oe.py` — `-i` metavar `CLIENT` + help, `--org` flag, standalone guard.
- `odoo_env/client.py` — `_is_full_git_url()`, `build_repo_url()`, `_resolve_install_url()`, wiring.
- `odoo_env/test_helpers.py` — `org` default in `MockArgs`.
- `odoo_env/test_config.py` (new), `odoo_env/test_client.py`, `odoo_env/test_oe.py`.
