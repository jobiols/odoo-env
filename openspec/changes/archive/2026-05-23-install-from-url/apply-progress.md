# Apply Progress: install-from-url

## Status: COMPLETE ✅

All 10 tests pass. Full suite (92 tests) passes with zero regressions.

## TDD Cycle Evidence

### Phase 1: Infrastructure (Task 1.1)
- **File created**: `odoo_env/test_client.py`
- **Setup**: Mocked OeConfig, subprocess.run, get_manifest_from_struct, check_common, check_v2
- **Verification**: Test file discovered by unittest runner

### Phase 2: RED — 10 tests written, 4 RED / 6 GREEN

| Test | RED/GREEN | Reason |
|------|-----------|--------|
| `test_install_bool_skips_url` | 🔴 RED | `subprocess.run` called with `True` as URL — **the bug** |
| `test_install_none_skips_url` | 🟢 GREEN | None is falsy, existing code already skips URL path |
| `test_existing_client_path_skips_url_bool` | 🟢 GREEN | client_path exists, else branch correctly used |
| `test_existing_client_path_skips_url_str` | 🟢 GREEN | client_path exists, URL skipped |
| `test_invalid_url_raises_oe_error` | 🔴 RED | No URL validation — got ValueError instead of OeError |
| `test_empty_url_raises_oe_error` | 🔴 RED | No URL validation — got ValueError instead of OeError |
| `test_url_success_saves_client_path` | 🔴 RED | `save_client_path` not called in current code |
| `test_url_no_manifest_returns_none` | 🟢 GREEN | No manifest → returns None (existing behavior) |
| `test_url_str_calls_get_manifest_from_url` | 🟢 GREEN | String install already forwards to URL path |
| `test_url_clone_failure_propagates` | 🟢 GREEN | Exception propagation + no save on failure (existing) |

### Phase 3: GREEN — 3 implementation tasks, 10/10 GREEN

| Task | Change | Lines |
|------|--------|-------|
| 3.1 | `if self._args.install:` → `if isinstance(self._args.install, str):` | 1 |
| 3.2 | URL validation block (git@/https:// check) | 4 |
| 3.3 | Capture `manifest_dir`, conditional `save_client_path` call | 3 |

### Phase 4: VERIFY

```bash
PYTHONPATH=/home/jobiols/tmp/odoo-env venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'
```

```
Ran 92 tests in 0.064s
OK
```

- 10 new tests: all pass
- 82 existing tests: all pass
- **Zero regressions**

## Files Changed

| File | Change | Lines |
|------|--------|-------|
| `odoo_env/client.py` | isinstance guard + URL validation + save_client_path | ~8 |
| `odoo_env/test_client.py` | NEW — 10 test methods | ~230 |

## Spec Compliance

| REQ | Scenarios | Test(s) | Status |
|-----|-----------|---------|--------|
| REQ-INSTALL-001 | install=True skips URL, install=None skips URL | test_install_bool_skips_url, test_install_none_skips_url | ✅ |
| REQ-INSTALL-002 | String URL forwarded to get_manifest_from_url | test_url_str_calls_get_manifest_from_url | ✅ |
| REQ-INSTALL-003 | Valid https://, git@ accepted; invalid/empty raises OeError | test_invalid_url_raises_oe_error, test_empty_url_raises_oe_error | ✅ |
| REQ-INSTALL-004 | save_client_path on success, not on failure | test_url_success_saves_client_path, test_url_no_manifest_returns_none, test_url_clone_failure_propagates | ✅ |
| REQ-INSTALL-005 | client_path exists → URL skipped (bool and str) | test_existing_client_path_skips_url_bool, test_existing_client_path_skips_url_str | ✅ |
| REQ-INSTALL-006 | Temp directory cleanup | Guaranteed by TemporaryDirectory; verified by tests 2.4+2.5 | ✅ |
| REQ-INSTALL-007 | Existing project skip with boolean -i | test_existing_client_path_skips_url_bool | ✅ |

## Deviations from Design

None. Implementation matches design.md exactly.

## Remaining Tasks

None. All tasks (1.1 through 4.2) completed.
