# Client Manifest Resolution Specification

## Purpose

This specification defines how the `Client` class resolves the Odoo project manifest
(`__manifest__.py`) for a given client name. It covers both filesystem-based resolution
and URL-based first-install resolution, including the `-i` flag behavior.

## Requirements

### Requirement: REQ-INSTALL-001 — Boolean guard for get_manifest

The system MUST NOT call `get_manifest_from_url()` when `self._args.install` is not a
string. The guard MUST use `isinstance(self._args.install, str)` as the discriminator.

#### Scenario: Install flag is boolean True (no URL)

- GIVEN a Client instance with `self._args.install` set to the boolean `True`
- AND `OeConfig().get_client_path(self._name)` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST NOT be invoked
- AND `get_manifest()` MUST proceed to filesystem-based manifest resolution via
  `get_manifest_from_struct()`

#### Scenario: Install flag is None (not passed)

- GIVEN a Client instance with `self._args.install` set to `None`
- AND `OeConfig().get_client_path(self._name)` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST NOT be invoked
- AND `get_manifest()` MUST proceed to filesystem-based manifest resolution via
  `get_manifest_from_struct()`

### Requirement: REQ-INSTALL-002 — URL string forwarding to get_manifest_from_url

When `self._args.install` is a string and no `client_path` is configured, the system MUST
forward that string as the URL argument to `get_manifest_from_url()`.

#### Scenario: Install flag is a git URL string

- GIVEN a Client instance with `self._args.install` set to
  `"git@github.com:org/repo.git"`
- AND `OeConfig().get_client_path(self._name)` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST be called
- AND the URL `"git@github.com:org/repo.git"` MUST be passed as the clone source
- AND the manifest returned by `get_manifest_from_url()` MUST be returned by
  `get_manifest()`

### Requirement: REQ-INSTALL-003 — URL validation in get_manifest_from_url

The `get_manifest_from_url()` method MUST validate the URL argument before executing
`git clone`. The URL MUST be a non-empty string starting with `git@` or `https://`. If
validation fails, the method MUST raise `OeError`.

#### Scenario: Valid HTTPS URL

- GIVEN `self._args.install` is `"https://github.com/org/repo.git"`
- WHEN `get_manifest_from_url()` is called
- THEN the URL MUST pass validation
- AND `git clone --depth 1 https://github.com/org/repo.git <tmpdir>` MUST be executed

#### Scenario: Valid git@ URL

- GIVEN `self._args.install` is `"git@github.com:org/repo.git"`
- WHEN `get_manifest_from_url()` is called
- THEN the URL MUST pass validation
- AND `git clone --depth 1 git@github.com:org/repo.git <tmpdir>` MUST be executed

#### Scenario: Invalid URL — does not start with git@ or https://

- GIVEN `self._args.install` is `"not-a-valid-url"`
- WHEN `get_manifest_from_url()` is called
- THEN an `OeError` MUST be raised
- AND the error message MUST indicate the URL is invalid

#### Scenario: Invalid URL — empty string

- GIVEN `self._args.install` is `""`
- WHEN `get_manifest_from_url()` is called
- THEN an `OeError` MUST be raised
- AND the error message MUST indicate the URL is invalid

### Requirement: REQ-INSTALL-004 — Save client_path on successful URL-based resolution

After successful URL-based manifest resolution, the system SHOULD persist the resolved
`client_path` via `OeConfig().save_client_path()` so that subsequent `-i` calls (without
URL) find the project without re-cloning.

#### Scenario: Successful URL clone and manifest load

- GIVEN a valid git URL that results in a successful `git clone` and a valid manifest
- WHEN `get_manifest_from_url()` resolves the manifest successfully
- THEN `OeConfig().save_client_path(self._name, <resolved_path>)` SHOULD be called
- AND subsequent `-i` calls without a URL MUST find the client via `OeConfig`

#### Scenario: Failed git clone — client_path NOT saved

- GIVEN a valid-format URL that references a non-existent repository
- WHEN `git clone` fails (raises `subprocess.CalledProcessError`)
- THEN `OeConfig().save_client_path()` MUST NOT be called
- AND no partial configuration state MUST be left behind

### Requirement: REQ-INSTALL-005 — First-install-only guard

URL-based manifest resolution MUST only trigger when no `client_path` is already
configured for the client name. When `client_path` exists, the system MUST use it
regardless of whether `-i` was passed with or without a URL.

#### Scenario: client_path already configured, -i passed with URL

- GIVEN `OeConfig().get_client_path(self._name)` returns a valid path
- AND `self._args.install` is a valid git URL string
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST NOT be called
- AND the manifest MUST be resolved from the configured `client_path` via
  `get_manifest_from_struct()`

#### Scenario: client_path already configured, -i passed without URL

- GIVEN `OeConfig().get_client_path(self._name)` returns a valid path
- AND `self._args.install` is the boolean `True`
- WHEN `get_manifest()` is called
- THEN the manifest MUST be resolved from the configured `client_path` via
  `get_manifest_from_struct()`
- AND `get_manifest_from_url()` MUST NOT be called

### Requirement: REQ-INSTALL-006 — Temp directory cleanup

The temporary directory created for git cloning MUST be cleaned up after manifest
loading, regardless of success or failure. This is handled by the existing
`tempfile.TemporaryDirectory()` context manager; the implementation MUST preserve this
behavior.

#### Scenario: Temporary directory cleanup after successful clone

- GIVEN a valid git URL
- WHEN `get_manifest_from_url()` completes successfully (returns a manifest dict)
- THEN the temporary directory created by `TemporaryDirectory()` MUST be removed

#### Scenario: Temporary directory cleanup after clone failure

- GIVEN a valid-format URL that causes `git clone` to fail
- WHEN `get_manifest_from_url()` raises an exception
- THEN the temporary directory MUST be cleaned up by the `TemporaryDirectory` context
  manager

### Requirement: REQ-INSTALL-007 — Existing project skip

When a `client_path` is already saved for the client, the system MUST skip URL-based
resolution entirely and resolve from the known path. This is the normal update/reinstall
path.

#### Scenario: Re-running install on existing project with boolean -i

- GIVEN a Client where `OeConfig().get_client_path(self._name)` returns a valid path
- AND `self._args.install` is the boolean `True`
- WHEN `get_manifest()` is called
- THEN the manifest MUST be resolved from the configured `client_path`
- AND `get_manifest_from_url()` MUST NOT be called
