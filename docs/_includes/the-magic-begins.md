## THE MAGIC BEGINS, From a fresh VPS to an installed odoo system

Start fresh, this example was build with Ubuntu Server 20.04 LTS

```bash
# start by upgrading the system
sudo apt update && sudo apt upgrade -y

# check if python 3 is installed
python3 -V

# if not installed do it
sudo apt install python3 -y

# install distutils
sudo apt install python3-distutils -y

# install pip
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

# test pip
pip -V

# install odoo-env
sudo pip install odoo-env

# install docker
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# install docker composer
sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
#  Apply executable permissions to the binary:
sudo chmod +x /usr/local/bin/docker-compose

# test tools
oe -h -v
sd --version
docker-compose --version
```

Ok this is all we need in the host, now begin creating a project

You have to select a short and memorable project name and please it must be unique for you.
We selected **myproject** as proyect name, then a minimum manifest working will be:

```python
    ##############################################################################
    #    Copyright (C) 2021 jeo Software  (http://www.jeosoft.com.ar)
    #    All Rights Reserved.
    ##############################################################################

{
    'name': 'myproject',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'summary': "Project example for v13 CE",
    'author': "jeo Software",
    'license': 'AGPL-3',
    'depends': [],
    'installable': True,
    'application': False,

    'env-ver': '2',

    'git-repos': [
        'https://github.com/jobiols/cl-myproject.git',
        'https://github.com/ingadhoc/odoo-argentina.git',
    ],

    'docker-images': [
        'odoo jobiols/odoo-jeo:13.0',
        'postgres postgres:10.1-alpine',
        'nginx nginx'
    ]
}
```

You can find this project at https://github.com/jobiols/cl-example.git branch 13.0

Then go to your VPS and clone this:

    git clone https://github.com/jobiols/cl-myproject.git

cd inside the repo and issue this command

    oe -i -c myproject

Then you can find a directory structure as this

    /odoo_ar
    ├── odoo-13.0
        └── myproject
            ├── config
            ├── data_dir
            ├── log
            ├── postgresql
            └── sources
                ├── cl-myproject
                └── odoo-argentina

You can remove the proyect you clone at first as it will not be used anymore, and can
lead to confusion. The useful one is in sources/

Then issue the command:

    oe -R -r --nginx

This will download all the necesary images and start them.

The odoo database manager starts blocked in nginex, so you have to comment some lines at the bottom of /odoo_ar/nginx/conf/nginx.conf

    # Block database manager and selector
    location ~* /web/database/manager {
            return 404;
    }
    location ~* /web/database/selector {
            return 404;
    }

This will unblock the database manager and let you start working with odoo databases.

now some commands:

Restart odoo

    oe -s -r

Stop all images

    sd rmall

Start all again

    oe -R -r --nginx

Update all repositories

    oe -i

Pull all images

    oe -p

Update odoo database

    oe -u


Enough for today stay tuned, more documentation on the way.
Jorge 2020-03-04
