# Client Manifest Resolution Specification

## Purpose

This specification defines how the `Client` class resolves the Odoo project manifest
(`__manifest__.py`) for a given client name. It covers filesystem-based resolution,
URL-based first-install resolution, and **client-name-based** first-install resolution
(building a canonical repository URL from a bare client name), including the `-i` flag
behavior.

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
forward that string to `get_manifest_from_url()`, which resolves it into a git URL (see
REQ-INSTALL-008) before cloning.

#### Scenario: Install flag is a git URL string

- GIVEN a Client instance with `self._args.install` set to
  `"git@github.com:org/repo.git"`
- AND `OeConfig().get_client_path(self._name)` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST be called
- AND the URL `"git@github.com:org/repo.git"` MUST be passed as the clone source
- AND the manifest returned by `get_manifest_from_url()` MUST be returned by
  `get_manifest()`

#### Scenario: Install flag is a bare client name

- GIVEN a Client instance with `self._args.install` set to `"labutic"`
- AND `OeConfig().get_client_path(self._name)` returns `None`
- WHEN `get_manifest()` is called
- THEN `get_manifest_from_url()` MUST be called
- AND the clone source MUST be the canonical URL built per REQ-INSTALL-008

### Requirement: REQ-INSTALL-003 — Input resolution and validation in get_manifest_from_url

The `get_manifest_from_url()` method MUST resolve `self._args.install` into a git URL
before executing `git clone`:

- If the value starts with `git@` or `https://`, it is treated as a full URL and used
  verbatim.
- Otherwise it is treated as a client name and converted to a canonical URL per
  REQ-INSTALL-008 (which includes the validation/normalization in REQ-INSTALL-010).

The resolved URL MUST be a non-empty string starting with `git@` or `https://`. If the
input cannot be resolved to a valid URL (e.g. empty string, or an invalid client name),
the method MUST raise `OeError`.

#### Scenario: Valid HTTPS URL used verbatim

- GIVEN `self._args.install` is `"https://github.com/org/repo.git"`
- WHEN `get_manifest_from_url()` is called
- THEN the value MUST be used verbatim as the clone source
- AND `git clone --depth 1 https://github.com/org/repo.git <tmpdir>` MUST be executed

#### Scenario: Valid git@ URL used verbatim

- GIVEN `self._args.install` is `"git@github.com:org/repo.git"`
- WHEN `get_manifest_from_url()` is called
- THEN the value MUST be used verbatim as the clone source
- AND `git clone --depth 1 git@github.com:org/repo.git <tmpdir>` MUST be executed

#### Scenario: Bare client name resolved to canonical URL

- GIVEN `self._args.install` is `"labutic"`
- AND the configured/default organization is `"quilsoft-org"`
- WHEN `get_manifest_from_url()` is called
- THEN the clone source MUST be `"git@github.com:quilsoft-org/cl-labutic.git"`
- AND `git clone --depth 1 git@github.com:quilsoft-org/cl-labutic.git <tmpdir>` MUST be
  executed

#### Scenario: Invalid input — empty string

- GIVEN `self._args.install` is `""`
- WHEN `get_manifest_from_url()` is called
- THEN an `OeError` MUST be raised
- AND the error message MUST indicate the input is invalid

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
regardless of whether `-i` was passed with or without a URL/name.

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

### Requirement: REQ-INSTALL-008 — Canonical repository URL from client name

The system MUST build a canonical git repository URL from a bare client name using the
fixed template:

```
git@github.com:<organization>/cl-<client>.git
```

The `cl-` prefix MUST be fixed (not configurable). The `<organization>` MUST be resolved
per REQ-INSTALL-009. The `<client>` MUST be the validated, lowercased client name per
REQ-INSTALL-010.

#### Scenario: Build canonical URL with default organization

- GIVEN the organization resolves to `"quilsoft-org"`
- AND the client name is `"labutic"`
- WHEN the canonical URL is built
- THEN the result MUST be `"git@github.com:quilsoft-org/cl-labutic.git"`

#### Scenario: Build canonical URL with configured organization

- GIVEN the organization resolves to `"acme-org"`
- AND the client name is `"labutic"`
- WHEN the canonical URL is built
- THEN the result MUST be `"git@github.com:acme-org/cl-labutic.git"`

### Requirement: REQ-INSTALL-009 — Organization configuration

The organization name MUST be resolvable from configuration with this precedence:

1. The `--org <name>` command-line flag (when provided), which MUST be persisted to
   `oe_config.yaml` under the `organization` key.
2. The `organization` key already present in `oe_config.yaml`.
3. The default value `"quilsoft-org"` when neither of the above is available.

When the default `"quilsoft-org"` is used because the `organization` key is missing from
the configuration, the system MUST persist `organization: quilsoft-org` into
`oe_config.yaml`.

Passing `--org <name>` as the only action (no other action flag such as `-i`, `-u`, etc.)
MUST persist the organization and return without performing any further action, mirroring
the behavior of `--base-dir`.

#### Scenario: Organization from --org flag is persisted

- GIVEN `oe --org acme-org` is invoked with no other action flag
- WHEN the command is processed
- THEN `organization: acme-org` MUST be persisted to `oe_config.yaml`
- AND the command MUST return without performing an install or other action

#### Scenario: Organization read from existing config

- GIVEN `oe_config.yaml` contains `organization: acme-org`
- AND `--org` is not passed
- WHEN the organization is resolved
- THEN the resolved organization MUST be `"acme-org"`

#### Scenario: Missing organization falls back to default and is persisted

- GIVEN `oe_config.yaml` does NOT contain an `organization` key
- AND `--org` is not passed
- WHEN the organization is resolved
- THEN the resolved organization MUST be `"quilsoft-org"`
- AND `organization: quilsoft-org` MUST be persisted to `oe_config.yaml`

### Requirement: REQ-INSTALL-010 — Client-name validation and normalization

When a bare client name is provided to `-i`, the system MUST validate and normalize it
before building the canonical URL:

- The name MUST NOT be empty.
- The name MUST NOT contain spaces or `/` characters; otherwise the system MUST raise
  `OeError` with a clear message.
- The name MUST be normalized to lowercase before being inserted into the canonical URL.

#### Scenario: Mixed-case client name is lowercased

- GIVEN the client name `"Labutic"`
- AND the organization resolves to `"quilsoft-org"`
- WHEN the canonical URL is built
- THEN the result MUST be `"git@github.com:quilsoft-org/cl-labutic.git"`

#### Scenario: Client name with a space is rejected

- GIVEN the client name `"foo bar"`
- WHEN the canonical URL is built
- THEN an `OeError` MUST be raised
- AND the error message MUST indicate the client name is invalid

#### Scenario: Client name with a slash is rejected

- GIVEN the client name `"foo/bar"`
- WHEN the canonical URL is built
- THEN an `OeError` MUST be raised
- AND the error message MUST indicate the client name is invalid
