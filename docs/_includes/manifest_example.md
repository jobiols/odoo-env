## THE PROJECT, where all the install information resides

What you need to know:

1. The project is an Odoo module.
2. This module has an extended manifest. Odoo does not read the extended keywords, so the module remains installable.
3. Odoo-env reads the manifest to know how to install the system.
4. The manifest holds:

    - **Odoo Version**: derived from the standard `version` keyword (e.g. `18.0.1.0.0` → branch `18.0`)
    - **env-ver**: manifest syntax version — must be `'2'`
    - **config / config-local**: parameters written to `odoo.conf` (prod vs debug)
    - **odoo-license**: `'CE'` (Community, default) or `'EE'` (Enterprise)
    - **port / longpolling_port**: HTTP and longpolling ports
    - **git-repos**: list of repositories to clone
    - **docker-images**: list of Docker images to pull
    - **prod_server**: SSH alias for production server (used by `--restore` workflows that involve SCP)

As a best practice, list all required modules in the `depends` key. Then the project not only
installs the environment but also documents which modules are needed. Run `oe -u` to install
them all in one shot — it runs `odoo-bin --update all --stop-after-init` inside the container.

## Syntax and examples

### `git-repos`

General syntax: `<repo-url> [<target-dir>[/<subdir>]] [-b <branch>]`

Odoo-env automatically determines the branch from the Odoo version in the manifest
(e.g. `version: '18.0.1.0.0'` → branch `18.0`). Override with `-b` when a repo doesn't
follow this convention.

**Basic example:**

```python
'git-repos': [
    'https://github.com/OCA/account-invoicing.git',
    'https://github.com/OCA/account-financial-tools.git',
]
```

Tree:
```
sources/
├── account-invoicing/
└── account-financial-tools/
```

**Renaming to avoid collisions:**

```python
'git-repos': [
    'https://github.com/OCA/account-invoicing.git oca-account-invoicing',
    'https://github.com/ingadhoc/account-invoicing.git adhoc-account-invoicing',
]
```

Tree:
```
sources/
├── oca-account-invoicing/
└── adhoc-account-invoicing/
```

**Single-module repos (nesting):**

```python
'git-repos': [
    'https://github.com/ctmil/meli_oerp.git ctmil/meli_oerp',
]
```

Tree:
```
sources/
└── ctmil/
    └── meli_oerp/
```

**Custom branch override:**

```python
'git-repos': [
    'https://github.com/ctmil/odoo_barcode.git ctmil/odoo_barcode -b main',
]
```

**SSH protocol (uses your SSH keys):**

```python
'git-repos': [
    'git@github.com:jobiols/private-repo.git private-repo -b 18.0',
]
```

### `docker-images`

Syntax: `<short-name> <image:tag>`

The `short-name` is how odoo-env refers to the image internally.
`odoo`, `postgres`, `aeroo`, and `nginx` are recognized names.

```python
'docker-images': [
    'odoo jobiols/odoo-jeo:18.0',
    'postgres postgres:17.5-alpine',
]
```

## Full manifest example

```python
{
    'name': 'myproject',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Example project for Odoo 18 CE',
    'author': 'jeo Software',
    'website': 'https://github.com/jobiols/odoo-env',
    'license': 'AGPL-3',
    'depends': [
        'sale_management',
        'account',
    ],
    'installable': True,
    'application': False,

    # ---------- odoo-env manifest (env-ver: 2) ----------

    'env-ver': '2',

    # Community or Enterprise
    'odoo-license': 'CE',

    # HTTP port
    'port': '8069',

    # Production server SSH alias (for backup transfer)
    'prod_server': 'ubuntu@my-server',

    # ---------- odoo.conf for production ----------
    'config': [
        'workers = 4',
        'max_cron_threads = 1',
        'limit_request = 8192',
        'limit_memory_soft = 2147483648',
        'limit_memory_hard = 2684354560',
        'limit_time_cpu = 60',
        'limit_time_real = 120',
        'admin_passwd = my-secure-password',
        'dbfilter = myproject',
        'db_maxconn = 64',
        'log_level = info',
        'logfile = /var/log/odoo/odoo.log',
    ],

    # ---------- odoo.conf for debug ----------
    'config-local': [
        'admin_passwd = admin',
        # In debug mode, workers/max_cron_threads/limit_time_* are
        # forced to 0 automatically by odoo-env.
    ],

    # ---------- Repositories ----------
    'git-repos': [
        'https://github.com/OCA/web.git oca-web',
        'https://github.com/OCA/server-tools.git oca-server-tools',
        'https://github.com/ingadhoc/odoo-argentina.git adhoc-odoo-argentina',
        'git@github.com:myorg/private-modules.git private-modules -b 18.0',
    ],

    # ---------- Docker images ----------
    'docker-images': [
        'odoo jobiols/odoo-jeo:18.0',
        'postgres postgres:17.5-alpine',
    ],

    # ---------- External system dependencies ----------
    'external_dependencies': {
        'python': ['requests', 'openpyxl'],
    },
}
```

## Configuration file

Odoo-env stores its own configuration at `~/.config/oe/oe_config.yaml`:

```yaml
base_dir: /odoo_ar/
client: myproject
environment: debug
last_version_check: '2026-05-23'
clients:
  - myproject: /odoo_ar/odoo-18.0/myproject/sources/cl-myproject/myproject
  - otherproj: /odoo_ar/odoo-16.0e/otherproj/sources/cl-otherproj/otherproj
```

- `base_dir` — root where all environments live (default `/odoo_ar/`). On macOS,
  set this to a path inside your home directory.
- `client` — the currently active client name.
- `environment` — `debug` or `prod`.
- `clients` — maps each client name to the path of its `__manifest__.py` directory.
  Odoo-env discovers and saves this automatically.
- `last_version_check` — date of last PyPI version check.
