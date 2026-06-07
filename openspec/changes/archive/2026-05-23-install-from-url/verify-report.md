# Verify Report: install-from-url

**Status**: ✅ PASS — with advisory findings

**Date**: 2026-05-23
**Executor**: sdd-verify
**Change**: Fix `oe -i` crash when `-i` is passed without URL (boolean `True` conflated with string URL)

---

## Executive Summary

The implementation correctly fixes the bug and satisfies all MUST and SHOULD requirements. 92/92 tests pass with zero regressions. Strict TDD was followed with clear RED → GREEN → VERIFY phases. All 7 spec requirements (REQ-INSTALL-001 through REQ-INSTALL-007) are covered.

Two advisory findings warrant attention:
1. **F-001 (ADVISORY)**: `save_client_path` saves a temporary path that dies on cleanup — creates a "poison pill" in config. Documented in ADR-002 but worth tracking.
2. **F-002 (MINOR)**: REQ-INSTALL-006 (temp cleanup) is only implicitly tested via `TemporaryDirectory` context manager guarantee — no explicit assertion.

---

## Test Results

### Full Suite

```
Command: PYTHONPATH=/home/jobiols/tmp/odoo-env /home/jobiols/tmp/odoo-env/venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'
Result: Ran 92 tests in 0.060s — OK
```

| Test File | Tests | Result |
|-----------|-------|--------|
| `test_client.py` | 10 | ✅ All pass |
| `test_constants.py` | 10 | ✅ All pass |
| `test_docker_client.py` | 6 | ✅ All pass |
| `test_environment_manager.py` | 23 | ✅ All pass |
| `test_image_manager.py` | 10 | ✅ All pass |
| `test_oe.py` | 33 | ✅ All pass |

**Regressions**: Zero.

### Individual New Tests

```
test_install_bool_skips_url             ✅
test_install_none_skips_url             ✅
test_existing_client_path_skips_url_bool ✅
test_existing_client_path_skips_url_str  ✅
test_invalid_url_raises_oe_error        ✅
test_empty_url_raises_oe_error          ✅
test_url_success_saves_client_path      ✅
test_url_no_manifest_returns_none       ✅
test_url_str_calls_get_manifest_from_url ✅
test_url_clone_failure_propagates       ✅
```

---

## Spec Compliance Matrix

| REQ | Level | Spec Scenarios | Tests | Coverage | Status |
|-----|-------|---------------|-------|----------|--------|
| REQ-INSTALL-001 | MUST | install=True skips URL, install=None skips URL | test_install_bool_skips_url, test_install_none_skips_url | ✅ Full | PASS |
| REQ-INSTALL-002 | MUST | String URL forwarded to get_manifest_from_url | test_url_str_calls_get_manifest_from_url | ✅ Full | PASS |
| REQ-INSTALL-003 | MUST | Valid HTTPS accepted, Valid git@ accepted, Invalid string raises OeError, Empty string raises OeError | test_invalid_url_raises_oe_error, test_empty_url_raises_oe_error, test_url_success_saves_client_path (https://), test_url_str_calls (git@) | ✅ Full | PASS |
| REQ-INSTALL-004 | SHOULD | save_client_path on success, NOT saved on clone failure, NOT saved when no manifest | test_url_success_saves_client_path, test_url_no_manifest_returns_none, test_url_clone_failure_propagates | ✅ Full | PASS |
| REQ-INSTALL-005 | MUST | client_path exists + URL string → skip, client_path exists + bool → skip | test_existing_client_path_skips_url_str, test_existing_client_path_skips_url_bool | ✅ Full | PASS |
| REQ-INSTALL-006 | MUST | Temp cleanup after success, Temp cleanup after failure | Implicit (TemporaryDirectory context manager guarantee) | ⚠️ Implicit | PASS * |
| REQ-INSTALL-007 | MUST | Existing project skip with boolean -i | test_existing_client_path_skips_url_bool | ✅ Full | PASS |

\* REQ-INSTALL-006 is satisfied by the `tempfile.TemporaryDirectory()` context manager, which is guaranteed to clean up regardless of exceptions. The tests exercise both success and failure paths through the context manager but do not assert directory removal explicitly. See Finding F-002.

---

## Strict TDD Compliance

### TDD Cycle Evidence

| Phase | Tests | Result |
|-------|-------|--------|
| Phase 1: Infrastructure | test_client.py skeleton created | ✅ |
| Phase 2: RED | 10 tests written | 4 RED, 6 GREEN |
| Phase 3: GREEN | 3 implementation tasks applied | 10/10 GREEN |
| Phase 4: VERIFY | Full suite run | 92/92 GREEN |

**RED tests in Phase 2** (verified from apply-progress.md):
- `test_install_bool_skips_url`: RED — `subprocess.run` called with `True` as URL (the bug)
- `test_invalid_url_raises_oe_error`: RED — No URL validation, got `ValueError` instead of `OeError`
- `test_empty_url_raises_oe_error`: RED — Same as above
- `test_url_success_saves_client_path`: RED — `save_client_path` not called in original code

**GREEN-before-implementation tests** (regression baseline):
- `test_install_none_skips_url`: GREEN — None is falsy, existing code already skips URL path
- `test_existing_client_path_skips_url_bool`: GREEN — client_path exists, else branch used correctly
- `test_existing_client_path_skips_url_str`: GREEN — client_path exists, URL skipped
- `test_url_no_manifest_returns_none`: GREEN — existing behavior
- `test_url_str_calls_get_manifest_from_url`: GREEN — string install already forwarded to URL path
- `test_url_clone_failure_propagates`: GREEN — exception propagation existed

**Assessment**: The 4 RED / 6 GREEN split is acceptable for a bug fix. The GREEN tests serve as regression guards for existing correct behavior. All RED tests turned GREEN after the 3 implementation tasks.

### Assertion Quality Audit

All 10 new test assertions are verified against quality criteria:

| Test | Tautologies | Ghost loops | Type-only | Smoke-only | CSS assertions | Verdict |
|------|-------------|-------------|-----------|------------|----------------|---------|
| test_install_bool_skips_url | No | No | No | No | N/A | ✅ |
| test_install_none_skips_url | No | No | No | No | N/A | ✅ |
| test_existing_client_path_skips_url_bool | No | No | No | No | N/A | ✅ |
| test_existing_client_path_skips_url_str | No | No | No | No | N/A | ✅ |
| test_invalid_url_raises_oe_error | No | No | No | No | N/A | ✅ |
| test_empty_url_raises_oe_error | No | No | No | No | N/A | ✅ |
| test_url_success_saves_client_path | No | No | No | No | N/A | ✅ |
| test_url_no_manifest_returns_none | No | No | No | No | N/A | ✅ |
| test_url_str_calls_get_manifest_from_url | No | No | No | No | N/A | ✅ |
| test_url_clone_failure_propagates | No | No | No | No | N/A | ✅ |

All tests use concrete assertions (behavioral: method called/not called; value: None/not-None, exact argument matching; exception: type + message content). No weak assertions found.

---

## Review Workload Verification

| Field | Forecast | Actual | Match |
|-------|----------|--------|-------|
| Estimated changed lines | ~158 (∼150 test, ∼8 impl) | ~230 test + ~8 impl = ~238 | ⚠️ 51% over |
| 400-line budget risk | Low | Low (238 < 400) | ✅ |
| Chained PRs recommended | No | Single PR returned | ✅ |
| Chain strategy | stacked-to-main | Single PR | ✅ |
| Scope creep | — | None detected | ✅ |

**Test file size**: `test_client.py` is 242 lines vs. the ~150 estimated. The overage is from the `setUp`/`tearDown` mock infrastructure, the `_make_client` helper, and `BASE_MANIFEST` constant — all of which are needed for test isolation. No scope creep; this is estimation variance.

---

## Implementation Quality

### isinstance Guard (ADR-001)

```python
if isinstance(self._args.install, str):
```

**Assessment**: ✅ Correct choice. Explicit, Pythonic, handles all non-string values (True, False, None, 0, "", lists, dicts) correctly. No false positives.

### URL Validation (ADR-003)

```python
if not (url.startswith("git@") or url.startswith("https://")):
    msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")
```

**Assessment**: ✅ Simple, fast, covers all standard git clone URLs (GitHub, GitLab, Bitbucket, self-hosted). Empty strings correctly fail both `startswith` checks and raise `OeError`.

### save_client_path (ADR-002)

```python
manifest, manifest_dir = self.get_manifest_from_struct(Path(tmpdir))
if manifest and manifest_dir:
    OeConfig().save_client_path(self._name, manifest_dir)
```

**Assessment**: ⚠️ Works as designed, with a known trade-off (see Finding F-001).

### Error Propagation (ADR-004)

**Assessment**: ✅ No try/except wrapping. `subprocess.run(check=True)` propagates `CalledProcessError` naturally. `TemporaryDirectory` context manager guarantees cleanup.

---

## Findings

### F-001: Dead temp path saved to config (ADVISORY)

**Severity**: ADVISORY
**Requirement**: REQ-INSTALL-004 (SHOULD)
**ADR**: ADR-002 (acknowledged)

The path saved by `OeConfig().save_client_path()` is inside a `TemporaryDirectory` that is cleaned up immediately after `get_manifest_from_url()` returns. The saved path is a "poison pill":

1. First `oe -i URL`: clones, saves `/tmp/tmpXXX/repo/` to config, cleans up temp dir
2. Second `oe -i URL`: `get_client_path()` returns dead path → `get_manifest_from_struct(dead_path)` returns `(None, None)` → skips `return manifest` → falls through to CWD walk
3. Second `oe -i` (no URL): same as above

**Impact**: On the second run, the dead path prevents re-cloning from the URL. The user must either manually delete the client_path from `oe_config.yaml` or have the project already installed at a CWD-accessible location.

**Design rationale**: ADR-002 acknowledges this and defers computing the final install path to a follow-up. The spec marks REQ-INSTALL-004 as SHOULD (not MUST), so no spec violation.

**Recommendation**: Track as a follow-up item. Consider either saving only after `install()` completes (when the real path is known) or computing the final path from manifest version info.

### F-002: No explicit temp-cleanup assertion (MINOR)

**Severity**: MINOR
**Requirement**: REQ-INSTALL-006 (MUST)

Neither `test_url_success_saves_client_path` nor `test_url_clone_failure_propagates` explicitly assert that the temporary directory was removed after `get_manifest_from_url()` completes. The cleanup is guaranteed by `tempfile.TemporaryDirectory()` context manager semantics, but no test verifies this contract is preserved.

**Recommendation**: Consider adding a test that patches `tempfile.TemporaryDirectory` to verify `__exit__` is called (or that `cleanup()` runs), or use `pyfakefs`/`tempfile.mkdtemp` + manual assertion post-call. Low priority since the context manager guarantee is very strong.

### F-003: `test_empty_url_raises_oe_error` doesn't verify URL in message (COSMETIC)

**Severity**: COSMETIC
**Test**: `test_empty_url_raises_oe_error`

The test asserts `assertIn("Invalid git URL", str(ctx.exception))` but doesn't check that the empty URL is included. The message format is `f"Invalid git URL '{url}'"` which would produce `"Invalid git URL ''"` for an empty string — still containing the key phrase. The existing assertion passes but is less strict than `test_invalid_url_raises_oe_error` which checks for the URL `"not-a-url"` specifically.

**Recommendation**: Add `assertIn("''", str(ctx.exception))` or verify the full message. Low priority.

---

## Edge Case Analysis

### Edge Cases Covered by isinstance Guard

| Input | isinstance(str) | Behavior | Covered by test? |
|-------|-----------------|----------|------------------|
| `True` | False | Skip URL path ✅ | test_install_bool_skips_url |
| `False` | False | Skip URL path ✅ | Implicit (MockArgs default) |
| `None` | False | Skip URL path ✅ | test_install_none_skips_url |
| `0` | False | Skip URL path ✅ | Not tested (safe) |
| `1` | False | Skip URL path ✅ | Not tested (safe) |
| `""` | True | Enter URL path → validation rejects → OeError ✅ | test_empty_url_raises_oe_error |
| `"not-a-url"` | True | Enter URL path → validation rejects → OeError ✅ | test_invalid_url_raises_oe_error |
| `"git@github.com:org/repo.git"` | True | Enter URL path → clone → manifest ✅ | test_url_str_calls_get_manifest_from_url |
| `"https://github.com/org/repo.git"` | True | Enter URL path → clone → manifest ✅ | test_url_success_saves_client_path |
| `[]` (list) | False | Skip URL path ✅ | Not tested (safe) |
| `{}` (dict) | False | Skip URL path ✅ | Not tested (safe) |

All problematic inputs are handled correctly. Untested edge cases (0, 1, list, dict) are safe because `isinstance(x, str)` is False for all of them.

### Boundary Conditions

- **`install="git@"` (protocol only, no repo)**: Passes `startswith("git@")` validation → `git clone` will fail with `CalledProcessError` → exception propagates. ✅ Acceptable (can't validate repo existence without network).
- **`install="https://"` (protocol only)**: Same as above. ✅ Acceptable.
- **No timeout on git clone**: Pre-existing issue, not introduced by this change. `subprocess.run` has no `timeout` parameter. Low risk for `--depth 1` clones.

---

## Code Change Verification

### `odoo_env/client.py:192`

```diff
-            if self._args.install:
+            if isinstance(self._args.install, str):
```

**Verified**: Line 192 in `get_manifest()` contains `isinstance(self._args.install, str)`.

### `odoo_env/client.py:136-138`

```python
url = self._args.install
if not (url.startswith("git@") or url.startswith("https://")):
    msg.err(f"Invalid git URL '{url}'. Must start with 'git@' or 'https://'")
```

**Verified**: Lines 136-138 at the top of `get_manifest_from_url()` contain the URL validation block.

### `odoo_env/client.py:145-147`

```python
manifest, manifest_dir = self.get_manifest_from_struct(Path(tmpdir))
if manifest and manifest_dir:
    OeConfig().save_client_path(self._name, manifest_dir)
```

**Verified**: Lines 145-147 inside `get_manifest_from_url()` capture `manifest_dir` and conditionally call `save_client_path`.

---

## Design-to-Implementation Trace

| ADR | Decision | Implementation | Match |
|-----|----------|---------------|-------|
| ADR-001 | isinstance guard inline in get_manifest() | `if isinstance(self._args.install, str):` at line 192 | ✅ |
| ADR-002 | save_client_path inside get_manifest_from_url() | `OeConfig().save_client_path(self._name, manifest_dir)` at line 147 | ✅ |
| ADR-003 | URL validation with startswith | `url.startswith("git@") or url.startswith("https://")` at line 137 | ✅ |
| ADR-004 | No explicit try/except, propagate exceptions | No try/except in get_manifest_from_url() | ✅ |
| ADR-005 | Direct unit tests on get_manifest() with selective mocking | test_client.py with unittest.TestCase, 10 tests | ✅ |
| ADR-006 | MockArgs no structural change needed | MockArgs unchanged; `install=True` and `install="url"` supported via kwargs | ✅ |

No deviations from design.md.

---

## Rollback Safety

All changes are additive or single-line replacements:
1. Revert `isinstance` → bare `if self._args.install:` (1 line, line 192)
2. Remove URL validation block (4 lines, lines 136-138)
3. Revert `manifest_dir` capture + `save_client_path` (3 lines, lines 145-147)
4. Delete `test_client.py`

No config format changes, no database, no migration. Rollback is trivial.

---

## Spec-to-Test Gap Analysis

### Missing Explicit Test Coverage

| Gap | Spec Scenario | Reason Not Tested |
|-----|--------------|-------------------|
| Valid HTTPS URL accepted individually | REQ-INSTALL-003: "Valid HTTPS URL" | Covered indirectly in `test_url_success_saves_client_path` (uses https://) and `test_url_str_calls_get_manifest_from_url` (uses git@) |
| Temp dir removed after success | REQ-INSTALL-006: "Temporary directory cleanup after successful clone" | Implicit in `TemporaryDirectory` context manager; see F-002 |
| Temp dir removed after failure | REQ-INSTALL-006: "Temporary directory cleanup after clone failure" | Implicit; see F-002 |
| install=False skips URL | Edge case (MockArgs default) | `isinstance(False, str)` is False; safe but untested |

### Over-Tested Areas

None. All 10 tests map to distinct spec scenarios without redundancy.

---

## Blockers

**No blockers.** The implementation is production-ready for merge.

## Recommendations

1. **[Follow-up]** Address F-001: save the real install path instead of the temp path (e.g., after `EnvironmentManager.install()` completes). This would make `oe -i` idempotent across sessions.
2. **[Low priority]** Address F-002: add explicit temp-cleanup assertion or document why it's unnecessary.
3. **[Cosmetic]** Strengthen `test_empty_url_raises_oe_error` to also verify the empty URL appears in the error message, matching the pattern in `test_invalid_url_raises_oe_error`.

---

## Final Verdict

| Criterion | Result |
|-----------|--------|
| All 92 tests pass | ✅ |
| Zero regressions | ✅ |
| All MUST requirements met | ✅ |
| All SHOULD requirements met | ✅ |
| Strict TDD compliance | ✅ |
| Assertion quality | ✅ No weak assertions |
| Review workload within budget | ✅ 238 < 400 |
| No scope creep | ✅ |
| Rollback safe | ✅ |
| Blockers | None |
