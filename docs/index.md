# Odoo Env — Docker-based Odoo Environment Manager

## Who is this for?

Odoo developers who want to install and manage Odoo instances quickly, consistently,
and without knowing Docker internals. Also useful for anyone deploying multiple Odoo
projects with different versions on the same machine.

## What is Odoo Env?

Odoo-env is a CLI tool (`oe`) that manages Docker-based Odoo environments. It reads
an Odoo module manifest to understand *everything* about a deployment — repositories,
Docker images, configuration — so a single manifest completely defines a project.

### Key Features

- **One manifest, one project** — all deployment info lives in an Odoo module's
  `__manifest__.py`
- **Install from URL** — `oe -i git@github.com:org/project.git` clones the repo,
  discovers the manifest automatically, and sets up the entire directory structure
- **Dual environments** — debug mode with WDB remote debugger vs production mode
  with optimized workers
- **Multi-version, multi-project** — run Odoo 11, 14, 17, and 19 side by side,
  switching between clients instantly with `-c`
- **Idempotent network** — Docker network `odoo-net` is created automatically on
  first use
- **Version check** — notifies you when a newer odoo-env is available on PyPI
- **EE and CE** — supports Community and Enterprise editions with automatic
  version-directory naming
- **Deploy keys** — generate SSH deploy key pairs for private repositories in
  production mode
- **Persistent config** — client name, database, environment mode, and base
  directory are saved in `~/.config/oe/oe_config.yaml`

## Quick Start

```bash
# Install
pipx install odoo-env

# Install a project from its repository
oe -i git@github.com:your-org/your-project.git -c yourclient

# Pull images and extract sources for debug
oe -p -i

# Start the environment
oe -R -r

# Update modules
oe -u

# Restore latest backup
oe --restore
```

## Full Command Reference

### Environment setup

| Command | Description |
|---|---|
| `-i [URL]` | Install environment. If a URL is given, clones the repo and auto-discovers the project name from the manifest. Without URL, updates all repositories for the configured client. |
| `-p` | Pull all Docker images declared in the client manifest. In debug mode, also extracts Odoo sources to the host. |
| `-w` | Create / overwrite the `odoo.conf` file from manifest config. |

### Runtime

| Command | Description |
|---|---|
| `-R` | Run environment containers: postgres, wdb (debug mode), aeroo (old Odoo versions). |
| `-r` | Run Odoo container. Detached in prod, interactive in debug. |
| `-S` | Stop environment containers. |
| `-s` | Stop Odoo container. |

### Database

| Command | Description |
|---|---|
| `-u` | Update modules. Use `-m module` for specific modules, or omit for all. Use `-d database` for non-default databases. |
| `--restore` | Restore a backup into the client database. By default restores the newest `.zip` in `backup_dir`. Use `-f` for a specific file, `-d` for a target database. |
| `--no-deactivate` | Skip database deactivation before restore. **Deprecated.** |
| `--create-test-db` | Create a `[client]_test` database: restores the test seed, then installs every module found in the repository. |

### Testing

| Command | Description |
|---|---|
| `-Q sale,stock` | Run Odoo tests on comma-separated module list. Uses the `[client]_test` database with `admin/admin` credentials. Add `-d database` to override. |

### Configuration

| Command | Description |
|---|---|
| `-c CLIENT` | Set the default client name. **Persistent** — saved in config. |
| `-d DATABASE` | Set the default database name. **Persistent.** |
| `--debug` | Set environment to debug mode. **Persistent.** |
| `--prod` | Set environment to production mode. **Persistent.** |
| `--base-dir PATH` | Set root directory for all environments (e.g. `/odoo_ar/`). **Persistent.** Does not require a client to be configured. |
| `--deploy-keys` | (Prod mode only) Generate SSH deploy key pairs for every private repository in the manifest. Prints public keys for adding to GitHub/GitLab. |

### Utilities

| Command | Description |
|---|---|
| `-H` | Show `odoo --help` from the Odoo image declared in the manifest. |
| `-V` | Show odoo-env version and exit. |
| `-v` | Verbose mode — prints every command before execution. |

## Directory Structure

```
/odoo_ar/                    # --base-dir (default)
└── odoo-18.0/               # version + optional 'e' for Enterprise
    └── clientname/
        ├── config/          # odoo.conf
        ├── data_dir/        # Odoo filestore
        ├── backup_dir/      # .zip backups for --restore
        ├── log/             # odoo.log
        ├── postgresql/      # PostgreSQL data volume
        └── sources/         # cloned git repositories
    ├── src/                 # Odoo core sources (debug, v11-v18)
    ├── site-packages/       # venv packages (debug, v19+)
    └── lib/                 # python libs (debug, v11-v18)
```

## Supported Odoo Versions

| Odoo | Python | Special notes |
|---|---|---|
| 8 – 10 | 2.7 | Uses `dist-packages`, `extra-addons` |
| 11 – 12 | 3.5 – 3.7 | Uses `dist-packages` |
| 13 | 3.7 | |
| 14 – 16 | 3.9 | Uses `src` + `lib` mounts |
| 17 | 3.10 | Uses `src` + `lib` mounts |
| 18 | 3.12 | Uses `src` + `lib` mounts |
| 19 | 3.10 (venv) | Uses `odoo-bin`, `src` + `site-packages` |

Docker images are hosted at [Docker Hub](https://registry.hub.docker.com/r/jobiols/odoo-jeo/tags)
and Dockerfiles at [GitHub](https://github.com/jobiols/docker-odoo-jeo).

## Manifest Format (env-ver: 2)

The manifest is a standard Odoo `__manifest__.py` with extra keys that only odoo-env
reads. Odoo itself ignores them, so the module remains installable.

Required keys:
- `name`, `version` (standard Odoo)
- `env-ver: '2'` (must be exactly '2')
- `git-repos` — list of repositories to clone
- `docker-images` — list of Docker images to pull

Optional keys:
- `odoo-license` — `'CE'` (default) or `'EE'`
- `config` — production odoo.conf parameters
- `config-local` — debug mode odoo.conf parameters
- `port` — Odoo HTTP port (default 8069)
- `longpolling_port` — longpolling port (default 8072)
- `prod_server` — SSH alias for `scp` backup transfer
- `external_dependencies` — system packages

See the [full manifest example](#the-project-where-all-the-install-information-resides) below.

---

Author: Jorge Obiols <jorge.obiols@gmail.com>

[GitHub repo](https://github.com/jobiols/odoo-env) ·
[Report an issue](https://github.com/jobiols/odoo-env/issues)

{% include manifest_example.md %}
{% include wich-images-to-use.md %}
{% include the-magic-begins.md %}
