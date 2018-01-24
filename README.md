[![Build Status](https://travis-ci.org/jobiols/odoo-env.svg?branch=master)](https://travis-ci.org/jobiols/odoo-env)
[![codecov](https://codecov.io/gh/jobiols/odoo-env/branch/master/graph/badge.svg)](https://codecov.io/gh/jobiols/odoo-env)

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
    Odoo Environment Manager v0.0.2 - by jeo Software <jorge.obiols@gmail.com>
    ==========================================================================
    
    optional arguments:
      -h, --help         show this help message and exit
      -i, --install-cli  Install client, requires -c option. Creates dir
                         structure, Pull repos and images, and generate odoo
                         config file
      -c CLIENT          Client name.
      -v, --verbose      Go verbose mode. Prints every command
      --debug            This option has the following efects: 1.- when doing an
                         update all, (option -u) it forces debug mode. 2.- When
                         running environment (option -R) it opens port 5432 to
                         access postgres server databases. 3.- when doing a pull
                         (option -p) it clones the full repo i.e. does not issue
                         --depth 1 to git
      --no-repos         Does not clone or pull repos used with -i or -p
      -R, --run-env      Run postgres and aeroo images.
      -r, --run-cli      Run client odoo, requires -c options
      --no-dbfilter      Eliminates dbfilter: The client can see any database.
                         Without this, the client can only see databases starting
                         with clientname_
      -S, --stop-env     Stop postgres and aeroo images.
      -s, --stop-cli     Stop client images, requires -c options.
      -u, --update-all   Update all requires -d -c and -m options. Use --debug to
                         force update with host sources
      -d DATABASE        Database name. Note that there is a dbfilter option by
                         default the database name must begin with clientname_
      -m MODULE          Module to update or all for updating all the registered
                         modules. You can specify multiple -m options. i.e. -m all
                         forall modules -m sales stock for updating sales and
                         stock modules


Tool to manage docker based odoo environments

jeo Software (c) 2018 jorge.obiols@gmail.com

This code is distributed under the AGPL license

Installation
------------
    some day : pip install docker-odoo-env
    
    for now: 
    clone the repo odoo-env in your home dir
    execute install_scripts from the data folder with sudo 
    
Changelog
---------

0.1.0   Nginx support, 
        Script to install docker (in script folder, execute manually)
        sd command (short for sudo docker plus some enhacements)
0.0.2   minor fixex
0.0.1   starting version