[![Build Status](https://travis-ci.org/jobiols/odoo-env.svg?branch=master)](https://travis-ci.org/jobiols/odoo-env)
[![codecov](https://codecov.io/gh/jobiols/odoo-env/branch/master/graph/badge.svg)](https://codecov.io/gh/jobiols/odoo-env)

Odooenv
=======

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
        ├── conf
        ├── log
        └── cert


Functionality
------------- 

    usage: oe.py [-h] [-i] [-w] [-R] [-r] [-S] [-s] [-u] [-c CLIENT] [-v]
                 [--debug] [--no-repos] [-d DATABASE] [-m MODULE] [--nginx]
                 [-Q repo] [--backup-list] [--restore] [-f BACKUP_FILE] [-H]
    
    ==========================================================================
    Odoo Environment Manager v0.8.13 - by jeo Software <jorge.obiols@gmail.com>
    ==========================================================================
    
    optional arguments:
      -h, --help          show this help message and exit
      -i, --install       Install, requires -c option. Creates dir structure, and
                          pull repos
      -w, --write-config  Write config file.
      -R, --run-env       Run postgres and aeroo images.
      -r, --run-cli       Run client odoo, requires -c option
      -S, --stop-env      Stop postgres and aeroo images.
      -s, --stop-cli      Stop client images, requires -c options.
      -u, --update-all    Update all requires -d -c and -m options. Use --debug to
                          force update with host sources
      -c CLIENT           Client name.
      -v, --verbose       Go verbose mode. Prints every command
      --debug             This option has the following efects: 1.- when doing an
                          update all, (option -u) it forces debug mode. 2.- When
                          running environment (option -R) it opens port 5432 to
                          access postgres server databases. 3.- when doing a pull
                          (option -p) it clones the full repo i.e. does not issue
                          --depth 1 to git
      --no-repos          Does not clone or pull repos used with -i or -p
      -d DATABASE         Database name.
      -m MODULE           Module to update or all for updating all the registered
                          modules. You can specify multiple -m options. i.e. -m
                          all forall modules -m sales stock for updating sales and
                          stock modules
      --nginx             Add nginx to installation: With -i creates nginx dir w/
                          sample config file. with -r starts an nginx container
                          linked to odoowith -s stops nginx containcer. You must
                          add certificates and review nginx.conf file.
      -Q repo             Perform QA running tests, argument are Repo to test.
                          Need -d, -m and -c options Note: for the test to run in
                          thedatabase there must be an admin user with password
                          admin
      --backup-list       List all backup files available for restore
      --restore           Restores a backup from backup_dir
      -f BACKUP_FILE      Filename to restore used with --restore
      -H, --server-help   List server help requires -c option

Tool to manage docker based odoo environments

jeo Software (c) 2019 jorge.obiols@gmail.com

This code is distributed under the MIT license

Installation
------------
    pip install odoo-env
    https://pypi.org/project/odoo-env/
    
Changelog
---------
- [0.8.13]  - Removing edm option (it was a bad idea), rewrite nginx 
              config to block /database/manager and /database/selector
- [0.8.12]  - fix version of wdb image to 3.2.5, latest does not work
- [0.8.11]  - Fix --nginx installation
- [0.8.10]  - Add --edm option to allow database manager on production
- [0.8.9]   - When installed from pip --nginx does not work
- [0.8.8]   - Disable database manager on login page in prod environment
- [0.8.7]   - Working on Python 2.7 to 3.7
- [0.8.6]   - Fix: when installing on prod make a Shallow Clone
- [0.8.5]   - Fix test (option -Q) failing to run
- [0.8.4]   - PyPi version increment
- [0.8.3]   - PyPi version increment
- [0.8.2]   - Docker installs at the end allowing abort 
- [0.8.1]   - Fix starting debug mode.
- [0.8.0]   - Use kozera image for wdb, write the nginx.conf with the
              proper client name.
- [0.7.4]   - New parameter to attach to a running containcer in sd
              Support for debug image in v11 (python3)
              data/install_scripts.sh improvements and fixes   
- [0.7.3]   - if odoo not in manifest do not start image instead showing 
              an error 
- [0.7.2]   - start aeroo on v > 9 
- [0.7.1]   - Revert again go https 
- [0.7.0]   - Change protocol from https to ssh in order to use ssh keys.
- [0.6.1]   - FIX working directory with version > 9. If odoo main 
              version was > 9 the directory added a dot ie /odoo-10.0./
- [0.6.0]   - deprecate dbfilter. 
- [0.5.4]   - illformed manifest causing crash 
- [0.5.3]   - restore database with bad image 
- [0.5.2]   - sd was not copied to /usr/local/bin 
- [0.5.1]   - change postgres container name to pg-<client name> 
- [0.5.0]   - support for non github repos, i.e. bitbucket, gitlab, etc 
- [0.4.6]   - Odoo v10 do not run aeroo, find manifest
- [0.4.5]   - Install_scripts now installs python and docker
- [0.4.4]   - Do not expose 8072 when using Nginx
- [0.4.3]   - No more rewriting config on update all
- [0.4.2]   - Expose longpolling port in debug mode
- [0.4.1]   - Fixes in test invocation 
- [0.4.0]   - Change QA invocation 
- [0.3.2]   - do not overwrite config while making QA 
- [0.3.1]   - Stop images instead of kill them on -s or -S 
- [0.3.0]   - Restore any automatic backup made with database_tools 
              module.
            - List all available backup files
            - write config file
            - add help option -H (odoo help)
- [0.2.1]   - bug On QA, expose port 1984 for debug purpoes with WDB
- [0.2.0]   - Quality Assurance support, 
            - Add command sd rmall for removing all docker images in 
              memory
- [0.1.0]   - Nginx support, 
            - Script to install docker (in script folder, for now you
              have to execute manually)
            - sd command (short for sudo docker plus some enhacements)
- [0.0.2]   - Minor fixes
- [0.0.1]   - Starting version
