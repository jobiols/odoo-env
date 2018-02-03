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
    │   ├── client_one
    │   │    ├── config             odoo.conf
    │   │    ├── data_dir           filestore
    │   │    ├── backup_dir         zip files with backups
    │   │    ├── log                odoo.log
    │   │    ├── postgresql         postgres database
    │   │    └── sources            custom sources
    │   ├── extra-addons            repos from image for debug
    │   ├── dist-local-packages     packages from image for debug
    │   └── dist-packages           pagkages from image for debug
    ├── nginx
    │   ├── conf
    │   ├── log
    │   └── cert
    └── postfix


Functionality so far
-------------------- 

    usage: oe.py [-h] [-i] [-w] [-R] [-r] [-S] [-s] [-u] [-c CLIENT] [-v]
                 [--debug] [--no-repos] [--no-dbfilter] [-d DATABASE] [-m MODULE]
                 [--nginx] [-Q repo test_file] [--backup-list] [--restore]
                 [-f BACKUP_FILE] [-H]
    
    ==========================================================================
    Odoo Environment Manager v0.3.2 - by jeo Software <jorge.obiols@gmail.com>
    ==========================================================================
    
    optional arguments:
      -h, --help            show this help message and exit
      -i, --install         Install, requires -c option. Creates dir structure,
                            and pull repos
      -w, --write-config    Write config file.
      -R, --run-env         Run postgres and aeroo images.
      -r, --run-cli         Run client odoo, requires -c option
      -S, --stop-env        Stop postgres and aeroo images.
      -s, --stop-cli        Stop client images, requires -c options.
      -u, --update-all      Update all requires -d -c and -m options. Use --debug
                            to force update with host sources
      -c CLIENT             Client name.
      -v, --verbose         Go verbose mode. Prints every command
      --debug               This option has the following efects: 1.- when doing
                            an update all, (option -u) it forces debug mode. 2.-
                            When running environment (option -R) it opens port
                            5432 to access postgres server databases. 3.- when
                            doing a pull (option -p) it clones the full repo i.e.
                            does not issue --depth 1 to git
      --no-repos            Does not clone or pull repos used with -i or -p
      --no-dbfilter         Eliminates dbfilter: The client can see any database.
                            Without this, the client can only see databases
                            starting with clientname_
      -d DATABASE           Database name. Note that there is a dbfilter option by
                            default the database name must begin with clientname_
      -m MODULE             Module to update or all for updating all the
                            registered modules. You can specify multiple -m
                            options. i.e. -m all forall modules -m sales stock for
                            updating sales and stock modules
      --nginx               Add nginx to installation: With -i creates nginx dir
                            w/ sample config file. with -r starts an nginx
                            container linked to odoowith -s stops nginx
                            containcer. You must add certificates and review
                            nginx.conf file.
      -Q repo test_file, --quality-assurance repo test_file
                            Perform QA running tests, arguments are Repo where
                            test lives, and yml/py test file to run (please
                            include extension). Need -d, -m and -c options Note:
                            for the test to run there must be an admin user with
                            password admin
      --backup-list         List all backup files available for restore
      --restore             Restores a backup from backup_dir
      -f BACKUP_FILE        Filename to restore used with --restore
      -H, --server-help     List server help requires -c option


Tool to manage docker based odoo environments

jeo Software (c) 2018 jorge.obiols@gmail.com

This code is distributed under the AGPL license

Installation
------------
    some day : pip install docker-odoo-env
    
    for now:
    cd
    git clone https://github.com/jobiols/odoo-env.git
    sudo ./odoo-env/data/install_scripts
 
    
Changelog
---------
- [0.3.2]   - do not overwrite config while making QA 
- [0.3.1]   - Stop images instead of kill them on -s or -S 
- [0.3.0]   - Restore any automatic backup made with database_tools 
              module.
            - List all available backup files
            - write config file
            - add help option -H
- [0.2.1]   - bug On QA, expose port 1984 for debug purpoes with WDB
- [0.2.0]   - Quality Assurance support, 
            - Add command sd rmall for removing all docker imagages in 
              memory
- [0.1.0]   - Nginx support, 
            - Script to install docker (in script folder, for now you
              have to execute manually)
            - sd command (short for sudo docker plus some enhacements)
- [0.0.2]   - Minor fixes
- [0.0.1]   - Starting version