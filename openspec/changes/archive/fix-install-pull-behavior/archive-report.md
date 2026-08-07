# Archive Report: fix-install-pull-behavior

**Status**: CLOSED
**Date Completed**: 2026-04-12
**Change**: fix-install-pull-behavior

---

## Summary

Two commands (`oe -i` and `oe -p`) had swapped responsibilities. Install was
silently destroying `dist-packages` / `dist-local-packages` in debug mode, and
pull was calling `docker run` instead of `docker pull`. This change corrects
both bugs by moving `extract_sources()` to its rightful place in `pull_images()`
and replacing the bogus `docker run` call with a proper `docker pull` call.

---

## What Changed

### Source files (3 modified)

| File | Change |
|------|--------|
| `odoo_env/services/docker_client.py` | Added `get_pull_command(image: str) -> list[str]` returning `["docker", "pull", image]` |
| `odoo_env/managers/image_manager.py` | `pull_images()` now calls `get_pull_command` instead of `get_run_command`; `extract_sources()` call in debug mode stays here |
| `odoo_env/managers/environment_manager.py` | Removed the `if OeConfig().debug: ret.extend(do_extract_sources(...))` block from `install()` entirely |

### Test files (3 new, 2 updated)

| File | Change |
|------|--------|
| `odoo_env/test_docker_client.py` | New — 3 tests covering REQ-01 to REQ-03 (`get_pull_command` correctness) |
| `odoo_env/test_image_manager.py` | New — 4 tests covering REQ-04 to REQ-07 (`pull_images` behavior) |
| `odoo_env/test_environment_manager.py` | New — 4 tests covering REQ-08 to REQ-11 (`install` idempotency) |
| `odoo_env/test_oe.py` (line 282) | Updated `test_pull_images` assertion from `docker run` to `docker pull` |
| `odoo_env/test_oe.py` (line 359) | Updated `test_download_image_sources` to call `oe.pull_images()` instead of `oe.install()` |

---

## Metrics

| Metric | Value |
|--------|-------|
| Requirements | 11/11 met |
| Tests passing | 28/28 |
| New test files | 3 |
| Modified source files | 3 |
| Updated existing tests | 2 |
| Regressions | 0 |
| TDD compliance | Strict — tests written before implementation |

---

## Behavioral Change (breaking for debug workflows)

Users who relied on `oe -i` to re-extract Python packages in debug mode must
now use `oe -p` instead. This is the correct behavior — `install` is
idempotent directory scaffolding, `pull` is what triggers image extraction.

---

## Artifacts

- `proposal.md` — intent, scope, risks, out-of-scope
- `spec.md` — 11 requirements + acceptance scenarios + test mapping
- `tasks.md` — 9 tasks, strict TDD order (tests-first)
- `verify-report.md` — 11/11 PASS, 28/28 tests green, one cosmetic suggestion
- `archive-report.md` — this file
