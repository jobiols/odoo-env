# Proposal: install-by-client-name

## Intent

Let `oe -i` accept a bare **client name** instead of requiring a full git URL.

Project repositories follow a canonical, fixed shape:

```
git@github.com:<organization>/cl-<client>.git
```

The only part that changes between clients is the client name. So the user
should be able to type:

```
oe -i labutic
```

and the tool builds `git@github.com:quilsoft-org/cl-labutic.git` automatically.

The organization is read from a new persistent config parameter (`organization`),
settable via a new `--org` flag, and defaulting to `quilsoft-org` when absent.

Full git URLs MUST keep working unchanged for backward compatibility.

## Scope

### In scope

- New canonical-URL builder: `git@github.com:<organization>/cl-<client>.git`,
  with the `cl-` prefix fixed/hardcoded.
- `oe -i <name>` resolution: if the value starts with `git@` or `https://`, use
  it verbatim (current behavior); otherwise treat it as a client name and build
  the canonical URL.
- New persistent config key `organization`:
  - new `--org <name>` flag (persistent, mirrors `--base-dir`);
  - default `quilsoft-org` when the key is missing AND `--org` is not passed;
  - when the default is used because the key is missing, it MUST be written
    (persisted) into `oe_config.yaml`.
- Client-name validation: reject names containing spaces or `/` with a clear error.
- Normalize the client name to lowercase before building the URL.
- Update `-i` argparse `metavar` from `REPO_URL` to `CLIENT` and rewrite its help.
- `oe --org <name>` alone (no action flag) MUST persist and return, like `--base-dir`.
- Unit tests covering URL building, org resolution/default/persist, validation,
  lowercase normalization, and backward-compatible full-URL pass-through.

### Out of scope

- Making the `cl-` prefix configurable (explicitly chosen fixed).
- Changing the manifest discovery / clone flow beyond the input URL it receives.
- Changing `EnvironmentManager.install()` orchestration.
- Supporting hosts other than `github.com` or protocols beyond `git@`/`https://`.
- Changing `-i` on existing/installed projects (still updates from manifest).

## Affected modules

| Module | Impact |
|---|---|
| `odoo_env/oe.py` — `parse_args()` | Change `-i` metavar/help; add `--org` flag; include `--org` in the standalone-persist guard. |
| `odoo_env/config.py` — `OeConfig` | Add `organization` getter (default + persist-on-missing), `save_organization()`, persist `args.org` in `persist_config()`. |
| `odoo_env/client.py` — install path | Resolve install value to a URL via a new builder; validate/normalize client name; keep full-URL pass-through. |
| `odoo_env/test_client.py`, `odoo_env/test_oe.py` | New/updated tests; revise the two tests that assumed any non-URL string is invalid. |
| `openspec/specs/client/spec.md` | Update REQ-INSTALL-003 and add REQ-INSTALL-008/009/010 (client-name resolution, org config, validation/normalize). |

## Current behavior

```
oe -i                          # args.install = True  → repos from manifest
oe -i git@github.com:org/repo.git   # args.install = str → clone URL, read manifest
oe -i labutic                  # args.install = "labutic" → treated as URL → git clone "labutic" → CRASH / invalid URL error
```

## Proposed behavior

```
oe -i                          # unchanged: repos from manifest
oe -i git@github.com:org/repo.git   # unchanged: full URL used verbatim
oe -i https://github.com/org/repo.git  # unchanged: full URL used verbatim
oe -i labutic                  # → git@github.com:<org>/cl-labutic.git  (org from config or default quilsoft-org)
oe -i Labutic                  # → git@github.com:<org>/cl-labutic.git  (lowercased)
oe -i "foo bar"                # → error: invalid client name
oe --org acme-org              # persist organization=acme-org and return
```

## Business rules

- Canonical template: `git@github.com:{organization}/cl-{client}.git` (prefix `cl-` fixed).
- `organization` resolution order: `--org` flag → config key → default `quilsoft-org`.
- When the default is used due to a missing key, persist `organization: quilsoft-org`.
- A "full URL" is any value starting with `git@` or `https://`.
- A client name is a simple token: no spaces, no `/`; normalized to lowercase.

## Rollback plan

The change is additive and localized. Rollback = revert the commit/PR. No data
migrations; the new `organization` config key is optional and ignored by old code.
Pre-existing full-URL and no-arg `-i` flows are untouched, so reverting cannot
break already-installed projects.
