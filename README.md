[![Codacy Badge](https://api.codacy.com/project/badge/Grade/349443f891184544b58e011ae3b6b465)](https://app.codacy.com/app/jobiols/odoo-env?utm_source=github.com&utm_medium=referral&utm_content=jobiols/odoo-env&utm_campaign=Badge_Grade_Settings)
[![Build Status](https://travis-ci.org/jobiols/odoo-env.svg?branch=master)](https://travis-ci.org/jobiols/odoo-env)
[![codecov](https://codecov.io/gh/jobiols/odoo-env/branch/master/graph/badge.svg)](https://codecov.io/gh/jobiols/odoo-env)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/44329410ef814e0085df49abeef4ff32)](https://www.codacy.com/app/jobiols/odoo-env?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=jobiols/odoo-env&amp;utm_campaign=Badge_Grade)
[![CodeFactor](https://www.codefactor.io/repository/github/jobiols/odoo-env/badge)](https://www.codefactor.io/repository/github/jobiols/odoo-env)

odoo-env
=========
jeo Software (c) 2020 jorge.obiols@gmail.com
This code is distributed under the MIT license

Tool to manage docker based odoo environments. This is a Dockerized 
Environment to manage Odoo. Two environments are provided debug and prod.

Directory structure

    /odoo_ar
    ├── odoo-11.0
    │   ├── client_one
    │   │    ├── config             odoo.conf
    │   │    ├── data_dir           filestore
    │   │    ├── backup_dir         zip files with backups
    │   │    ├── log                odoo.log
    │   │    ├── postgresql         postgres database
    │   │    └── sources            custom sources
    │   ├── dist-local-packages     packages from image for debug
    │   └── dist-packages           pagkages from image for debug
    └── nginx
        ├── conf
        ├── log
        └── cert

Functionality
------------- 

usage: oe [-h] [-i] [-p] [-w] [-R] [-r] [-S] [-s] [-u] [-c CLIENT] [-v]
          [--deactivate] [--debug] [--prod] [--no-repos] [-d DATABASE]
          [-m MODULE] [--nginx] [-Q repo] [--backup-list] [--restore]
          [-f BACKUP_FILE] [-H] [-V]

    ==========================================================================
    Odoo Environment Manager v0.10.0 - by jeo Software <jorge.obiols@gmail.com>
    ==========================================================================
    
    optional arguments:
      -h, --help          show this help message and exit
      -i, --install       Install. Creates dir structure, and pull all the
                          repositories declared in the client manifest. Use with
                          --debug to copy Odoo image sources to host
      -p, --pull-images   Pull Images. Download all images declared in client
                          manifest.
      -w, --write-config  Create / Overwrite config file.
      -R, --run-env       Run postgres and aeroo images.
      -r, --run-cli       Run odoo image
      -S, --stop-env      Stop postgres and aeroo images.
      -s, --stop-cli      Stop odoo image.
      -u, --update        Update modules to database. Use --debug to force update
                          with image sources. use -m modulename to update this
                          only module default is all use -d databasename to update
                          this database, default is clientname_default
      -c CLIENT           Set default client name. This option is persistent
      -v, --verbose       Go verbose mode. Prints every command
      --deactivate        Deactivate database before restore
      --debug             Set default environment mode to debugThis option has the
                          following efects: 1.- When doing an install it copies
                          the image sources to host and clones repos with
                          depth=1002.- When doing an update all, (option -u) it
                          forces update with image sources.This option is
                          persistent.
      --prod              Set default environment mode to productionThis option is
                          intended to install a production environment.This option
                          is persistent.
      --no-repos          Does not clone or pull repos when doing -i (install)
      -d DATABASE         Set default Database name.This option is persistent
      -m MODULE           Module to update. Used with -u (update) i.e. -m sale for
                          updating sale module -m all for updating all modules.
                          NOTE: if you perform -u without -m it asumes all modules
      --nginx             Add nginx to installation: Used with -i creates nginx
                          dir with config file. Used with -r starts an nginx
                          container linked to odoo.Used with -s stops nginx
                          container. If you want to add certificates review
                          nginx.conf file located in /odoo_ar/nginx/conf
      -Q repo             Perform QA running tests, argument are repository to
                          test. Need -d, -m and -c options Note: for the test to
                          run the database must be created with demo data and must
                          have admin user with password admin.
      --backup-list       List all backup files available for restore
      --restore           Restores a backup. it uses last backup and restores to
                          default database. You can change the backup file to
                          restore with -f option and change database name -d
                          option
      -f BACKUP_FILE      Filename to restore. Used with --restore. To get the
                          name of this file issue a --backup-list command.If
                          ommited the newest file will be restored
      -H, --server-help   Show odoo server help, it shows the help from the odoo
                          imagedeclared in the cliente manifest
      -V, --version       Show version number and exit.
Installation
------------
    sudo pip install odoo-env
    see proyect in https://pypi.org/project/odoo-env/
    
Changelog
---------
    - 0.10.0 New manifest syntax, backward compatible.
    - 0.9.14 improved creation of odoo.conf, i.e. detect cpu number and
      calculate workers.
    - 0.9.13 solved bug when creating nginx config file 
    - 0.9.12 Get last wdb vesion. Added a check to verify if there is 
    a new version available in pypi. Fixed copy sources to host. 
    - 0.9.11 The commands -c and --debug now are persistent. 
    - 0.8.35 Workaround for mdillon gis database
    - 0.8.32 Fix issue with first time installation
    - 0.8.30 Add cache file to fix performance issues when we have more 
    than 15 clients.
    - 0.8.29 Modify ssl certificate directories from letsencrypt, 
    support for oca/letsencript.
    - 0.8.27 Fix compatibility issues w/ python3
    - 0.8.22 When using the options -i together with --debug, the 
    dist_packages and extra_addons directories were created with the 
    image sources but in read-only mode. Now we give them write 
    permission and a git repository is added to verify if there were 
    modifications. Option -V is added to show the version.
    - 0.8.21 Many improvements on restore database.
    - 0.8.20 When option -d not present assume database = client_name + 
             "_prod" when option -m is not present asume default "all"
    - 0.8.19 Allow options -i and -w to work together
    - 0.8.18 add -p command 
    - 0.8.17 Fix bug in python3 installation 
    - 0.8.13 Removing edm option (it was a bad idea), rewrite nginx 
             config to block /database/manager and /database/selector
    - 0.8.12 fix version of wdb image to 3.2.5, latest does not work
    - 0.8.11 Fix --nginx installation
    - 0.8.10 Add --edm option to allow database manager on production
    - 0.8.9  When installed from pip --nginx does not work
    - 0.8.8  Disable database manager on login page in prod environment
    - 0.8.7  Working on Python 2.7 to 3.7
    - 0.8.6  Fix: when installing on prod make a Shallow Clone
    - 0.8.5  Fix test (option -Q) failing to run
    - 0.8.4  PyPi version increment
    - 0.8.3  PyPi version increment
    - 0.8.2  Docker installs at the end allowing abort 
    - 0.8.1  Fix starting debug mode.
    - 0.8.0  Use kozera image for wdb, write the nginx.conf with the       
             proper client name.
    - 0.7.4  New parameter to attach to a running containcer in sd. 
             Support for debug image in v11 (python3) 
             data/install_scripts.sh improvements and fixes   
    - 0.7.3  if odoo not in manifest do not start image instead showing 
             an error 
    - 0.7.2  start aeroo on v > 9 
    - 0.7.1  Revert again go https 
    - 0.7.0  Change protocol from https to ssh in order to use ssh keys.
    - 0.6.1  FIX working directory with version > 9. If odoo main 
             version was > 9 the directory added a dot ie /odoo-10.0./
    - 0.6.0  deprecate dbfilter. 
    - 0.5.4  illformed manifest causing crash 
    - 0.5.3  Restore database with bad image 
    - 0.5.2  sd was not copied to /usr/local/bin 
    - 0.5.1  change postgres container name to pg-<client name> 
    - 0.5.0  support for non github repos, i.e. bitbucket, gitlab, etc 
    - 0.4.6  Odoo v10 do not run aeroo, find manifest
    - 0.4.5  Install_scripts now installs python and docker
    - 0.4.4  Do not expose 8072 when using Nginx
    - 0.4.3  No more rewriting config on update all
    - 0.4.2  Expose longpolling port in debug mode
    - 0.4.1  Fixes in test invocation 
    - 0.4.0  Change QA invocation 
    - 0.3.2  do not overwrite config while making QA 
    - 0.3.1  Stop images instead of kill them on -s or -S 
    - 0.3.0  Restore any automatic backup made with database_tools module.
             List all available backup files write config file add help 
             option -H (odoo help)
    - 0.2.1  bug On QA, expose port 1984 for debug purpoes with WDB
    - 0.2.0  Quality Assurance support, Add command sd rmall for removing 
             all docker images in memory
    - 0.1.0  Nginx support, Script to install docker (in script folder, 
             for now you have to execute manually) sd command (short for 
             sudo docker plus some enhacements)
    - 0.0.2  Minor fixes
    - 0.0.1  Starting version
