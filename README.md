[![Build Status](https://travis-ci.org/jobiols/odoo-env.svg?branch=master)](https://travis-ci.org/jobiols/odoo-env)
[![codecov](https://codecov.io/gh/jobiols/docker-odoo-env/branch/master/graph/badge.svg)](https://codecov.io/gh/jobiols/docker-odoo-env)

Odooenv
=======

Warning
-------
This code is is under development (stay tuned)

Directory structure

    /odoo
    ├── odoo-9.0
    │   ├── glinsar
    │   │    ├── config               odoo.conf
    │   │    ├── data_dir             filestore
    │   │    ├── log                  odoo.log
    │   │    ├── postgresql           postgres database
    │   │    └── sources              custom sources
    │   ├── extra-addons         repos from image for debug
    │   ├── dist-local-packages  packages from image for debug
    │   └── dist-packages        pagkages from image for debug
    ├── nginx
    └── postfix


Functionality so far
--------------------- 
usage: oe.py [-h] [-i] [-c CLIENT] [-v] [--debug] [--no-repos] [-R] [-r]
             [--no-dbfilter] [-S] [-s] [-u] [-d DATABASE] [-m MODULE]

==========================================================================
Odoo Environment Manager v0.0.1 - by jeo Software <jorge.obiols@gmail.com>
==========================================================================

optional arguments:
  -h, --help         show this help message and exit
  -i, --install-cli  Install client, requires -c option. Creates dir
                     structure, Pull repos and images, and generate odoo
                     config file
  -c CLIENT          Client name.
  -v, --verbose      Go verbose mode. Prints every command
  --debug            This option has three efects: 1.- when doing an update
                     database, (option -u) it forces debug mode. 2.- When
                     running environment (option -R) it opens port 5432 to
                     access postgres server databases. 3.- when doing a pull
                     (option -p) it clones the full repo i.e. does not issue
                     --depth 1 to git
  --no-repos         Does not clone or pull repos used with -i or -p
  -R, --run-env      Run database and aeroo images.
  -r, --run-cli      Run client odoo, requires -c options
  --no-dbfilter      Eliminates dbfilter: The client can see any database.
                     Without this, the client can only see databases starting
                     with clientname_
  -S, --stop-env     Stop database and aeroo images.
  -s, --stop-cli     Stop client images, requires -c options.
  -u, --update-all   Update database requires -d -c and -m options. Use
                     --debug to force update with host sources
  -d DATABASE        Database name.
  -m MODULE          Module to update or all for updating all the registered
                     modules. You can specify multiple -m options.


Tool to manage docker based odoo environments

jeo Software (c) 2018 jorge.obiols@gmail.com

This code is distributed under the AGPL license

Installation
------------
    pip install docker-odoo-env
