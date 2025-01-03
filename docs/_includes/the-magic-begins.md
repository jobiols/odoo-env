## THE MAGIC BEGINS, From a fresh VPS to an installed odoo system

Start fresh, this example was build with Ubuntu Server 24.04 LTS

```bash
# start by upgrading the system
sudo apt update && sudo apt upgrade -y

# install pipx
sudo apt install pipx
pipx ensurepath

# install odoo-env
pipx install odoo-env
```
## install docker (easy way, DO NOT RECOMMENDED FOR PRODUCTION)
```
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
```
## install docker (best way DEBIAN)
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install latest Docker versin
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
## install docker (best way UBUNTU)
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install latest Docker versin
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
## test tools
- oe -v
- sd --version

# Installing project

Alright, this is everything we need on the host. Now, let's start creating a project. Choose a short, memorable, and unique name for your project.

For example, we chose **myproject** as the project name.
With this, a minimal working manifest would look like:"

```python
##########################################################################
#    Copyright (C) 2024 jeo Software  (http://www.jeosoft.com.ar)
#    All Rights Reserved.
##########################################################################

{
    'name': 'myproject',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': "Project example for v17 CE",
    'author': "jeo Software",
    'license': 'AGPL-3',
    'depends': [],
    'installable': True,
    'application': False,

    'env-ver': '2',
    'config': [
                'workers = 4,
                'max_cron_threads = 1',
                'admin_passwd = k0923%098',
                'proxy_mode = True',
                'list_db = False',
              ]
    'config-local': ['admin_passwd = admin',]
    'git-repos': [
        'https://github.com/jobiols/cl-myproject.git',
        'https://github.com/ingadhoc/odoo-argentina.git',
    ],

    'docker-images': [
        'odoo jobiols/odoo-jeo:17.0',
        'postgres postgres:14.13-alpine',
        'nginx nginx'
    ]
}
```

You can find this project at https://github.com/jobiols/cl-example.git branch 17.0

Go to your VPS or local machine and clone the project this way:

    oe -i -c https://github.com/jobiols/cl-myproject.git -b 17.0

oe will download the repository with the project and install it locally, generating the following directory structure.

    /odoo_ar
    └── odoo-17.0
        └── myproject
            ├── config
            ├── data_dir
            ├── log
            ├── postgresql
            └── sources
                ├── cl-myproject
                └── odoo-argentina

Then issue the command:

    oe -R -r

This will download all the necesary images and start the project

# some command examples

Restart odoo

    oe -s -r

Stop all images

    sd rmall

Start all again

    oe -R -r

Update all repositories

    oe -i

Pull all images

    oe -p

Update odoo database

    oe -u

Restore last backup

    oe --restore

Restore last production backup

    oe --restore --from-prod

Restore last production backup without deactivation (this may be dangerous)

    oe --restore --from-prod --no-deactivate


# Configuration File

odoo-env stores a configuration file at ~/.config/oe/oe_config.yaml
This file is maintained automatically by oe, although it's sometimes good to review it.

``` yaml
base_dir: /odoo/ar/
client: emafi
clients:
    - danone: /odoo/ar/odoo-14.0e/danone/sources/cl-danone/danone_default
    - atm: /odoo/ar/odoo-13.0/atm/sources/cl-atm/atm_default
    - villandry: /odoo/ar/odoo-13.0e/villandry/sources/cl-villandry/villandry_default
    - caepso: /odoo/ar/odoo-13.0e/caepso/sources/cl-caepso/caepso_default
    - emafi: /odoo/ar/odoo-13.0e/emafi/sources/cl-emafi/emafi_default
    - lopez: /odoo/ar/odoo-16.0e/lopez/sources/cl-lopez/lopez_default
environment: debug
last_version_check: '2023-09-27'
```

Note that base_dir starts at /odoo_ar/ by default, in some systems
as MAC OS this should be changed adding the first line base_dir: /your-base-dir
