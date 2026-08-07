## THE MAGIC BEGINS — From a fresh VPS to a running Odoo system

This example uses Ubuntu Server 24.04 LTS. Adapt for your distribution.

### 1. Prepare the host

```bash
# Upgrade the system
sudo apt update && sudo apt upgrade -y

# Install pipx (recommended way to install odoo-env)
sudo apt install pipx -y
pipx ensurepath

# Install odoo-env
pipx install odoo-env

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Add your user to the docker group (log out and back in afterwards)
sudo usermod -aG docker $USER

# Verify tools
oe -V
docker --version
```

### 2. Create a project

You need an Odoo module with an extended manifest. The simplest approach is to keep it in a
git repository so you can install with a single command.

**Minimal manifest** (`__manifest__.py`):

```python
{
    'name': 'myproject',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'My Odoo 18 project',
    'author': 'jeo Software',
    'license': 'AGPL-3',
    'depends': [],
    'installable': True,
    'application': False,

    'env-ver': '2',

    'git-repos': [
        'https://github.com/OCA/web.git',
    ],

    'docker-images': [
        'odoo jobiols/odoo-jeo:18.0',
        'postgres postgres:17.5-alpine',
    ],
}
```

### 3. Install the project

You can install from a local repo or directly from a remote URL:

```bash
# Option A: Install from a remote repository (auto-discovers project name)
oe -i git@github.com:your-org/myproject.git -c myproject

# Option B: If you already have the repo cloned locally
cd /path/to/myproject
oe -i -c myproject
```

This creates the directory structure under `--base-dir` (default `/odoo_ar/`):

```
/odoo_ar/
└── odoo-18.0/
    └── myproject/
        ├── config/
        ├── data_dir/
        ├── backup_dir/
        ├── log/
        ├── postgresql/
        └── sources/
            └── web/
```

> **Note:** After installation, the original cloned repo can be deleted — the working copy
> lives in `sources/`.

### 4. Pull images and extract sources (debug mode)

```bash
# Set debug mode
oe --debug

# Pull Docker images and extract Odoo sources to the host
oe -p -i

# Write the odoo.conf
oe -w

# Start the environment (postgres + wdb debugger) and Odoo
oe -R -r
```

Odoo starts in interactive mode with WDB attached. Open `http://localhost:8069` in your browser
and create a database. The default master password in debug mode is `admin`.

### 5. Production deployment

```bash
# Set production mode
oe --prod

# Install, pull images, start
oe -i -p -w
oe -R -r
```

In production, Odoo runs detached with optimized worker settings. Workers and cron threads are
calculated automatically from CPU count unless overridden in the manifest.

### 6. Day-to-day commands

```bash
# Restart Odoo
oe -s -r

# Stop everything
oe -S

# Start everything again
oe -R -r

# Update all repositories
oe -i

# Pull latest Docker images
oe -p

# Update all modules in the database
oe -u

# Update a specific module
oe -u -m sale

# Restore the latest backup
oe --restore

# Restore a specific backup file
oe --restore -f backup_2025_01_15.zip

# Restore to a different database
oe --restore -d myproject_test

# Generate deploy keys for private repos (production only)
oe --prod --deploy-keys

# Switch between projects
oe -c otherproject

# Run tests
oe -Q sale,stock -d myproject_test

# Show Odoo help from the container
oe -H

# Verbose mode — see every command
oe -v -R
```

### 7. Upgrading odoo-env

Odoo-env automatically checks PyPI for newer versions once per day and warns you if an
update is available.

```bash
pipx upgrade odoo-env
```

### 8. The configuration file

Everything that is persistent is stored in `~/.config/oe/oe_config.yaml`. You generally
don't need to edit it by hand — odoo-env manages it automatically.

```yaml
base_dir: /odoo_ar/
client: myproject
environment: debug
last_version_check: '2026-05-23'
clients:
  - myproject: /odoo_ar/odoo-18.0/myproject/sources/cl-myproject/myproject_default
```

To change the root directory on systems where `/odoo_ar/` doesn't work (e.g. macOS):

```bash
oe --base-dir /Users/you/odoo_ar/
```
