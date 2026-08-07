# Test Specification for install-from-url

## Purpose

This specification defines the test requirements for verifying the manifest resolution
chain changes introduced by the `install-from-url` change. These tests MUST exercise
`Client.get_manifest()` and `Client.get_manifest_from_url()` directly — not through the
existing mocked `Client.get_manifest` used by `OdooEnvTestCase`.

## Requirements

### Requirement: TEST-INSTALL-001 — Boolean guard: True does not trigger URL clone

The test suite MUST include a test case verifying that when `self._args.install` is
`True`, `get_manifest()` does NOT call `get_manifest_from_url()`.

#### Scenario: Verify isinstance guard with boolean True

- GIVEN a Client instance with `self._args.install = True`
- AND `OeConfig().get_client_path()` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST NOT be called
- AND `get_manifest()` MUST call `get_manifest_from_struct()` for filesystem resolution

### Requirement: TEST-INSTALL-002 — URL string triggers get_manifest_from_url

The test suite MUST include a test case verifying that when `self._args.install` is a
valid git URL string and no `client_path` exists, `get_manifest()` forwards the URL to
`get_manifest_from_url()`.

#### Scenario: Verify URL string forwarding

- GIVEN a Client instance with `self._args.install = "https://github.com/org/repo.git"`
- AND `OeConfig().get_client_path()` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST be called
- AND the URL `"https://github.com/org/repo.git"` MUST be used as the clone source

### Requirement: TEST-INSTALL-003 — Invalid URL raises OeError

The test suite MUST include a test case verifying that `get_manifest_from_url()` raises
`OeError` when given an invalid URL.

#### Scenario: Verify URL validation rejects malformed URLs

- GIVEN `self._args.install` is `"not-a-valid-url"`
- WHEN `get_manifest_from_url()` is called
- THEN an `OeError` MUST be raised

#### Scenario: Verify URL validation rejects empty strings

- GIVEN `self._args.install` is `""`
- WHEN `get_manifest_from_url()` is called
- THEN an `OeError` MUST be raised

### Requirement: TEST-INSTALL-004 — client_path saved after successful URL resolution

The test suite MUST include a test case verifying that after a successful URL-based
manifest resolution, `OeConfig().save_client_path()` is called with the correct
arguments.

#### Scenario: Verify save_client_path is called on success

- GIVEN `get_manifest_from_url()` clones successfully and returns a valid manifest
- WHEN the resolution completes
- THEN `OeConfig().save_client_path()` MUST be called with `(client_name, path)`

### Requirement: TEST-INSTALL-005 — Existing client_path skips URL resolution

The test suite MUST include a test case verifying that when `client_path` is already
configured, `get_manifest_from_url()` is not called even when `self._args.install` is a
string.

#### Scenario: Verify first-install-only guard

- GIVEN `OeConfig().get_client_path(self._name)` returns a valid path
- AND `self._args.install` is `"git@github.com:org/repo.git"`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST NOT be called
- AND the manifest MUST be resolved from the configured path

### Requirement: TEST-INSTALL-006 — All existing tests continue to pass

The existing 32 tests in `odoo_env/test_oe.py` MUST continue to pass after the code
changes, with zero regressions.

#### Scenario: Full test suite passes

- GIVEN the install-from-url code changes are applied
- WHEN the test suite is run with
  `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p 'test_*.py'`
- THEN all existing tests MUST pass
- AND all new manifest resolution tests MUST pass
