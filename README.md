![workflow](https://github.com/jobiols/odoo-env/actions/workflows/pre-commit.yml/badge.svg)
[![CodeFactor](https://www.codefactor.io/repository/github/jobiols/odoo-env/badge)](https://www.codefactor.io/repository/github/jobiols/odoo-env)

[Project documentation](https://jobiols.github.io/odoo-env/)

odoo-env
=========
jeo Software (c) 2024 jorge.obiols@gmail.com
This code is distributed under the MIT license.

Tool to manage docker based odoo environments. This is a Dockerized
Environment to manage Odoo. Two environments are provided debug and prod.

Directory structure

    /odoo_ar
    └── odoo-16.0
        ├── client_one
        │    ├── config             odoo.conf
        │    ├── data_dir           filestore
        │    ├── backup_dir         zip files with backups
        │    ├── log                odoo.log
        │    ├── postgresql         postgres database
        │    └── sources            custom sources
        ├── dist-local-packages     packages from image for debug
        └── dist-packages           pagkages from image for debug

Functionality
-------------

    usage: oe [-h] [-i] [-p] [-w] [-R] [-r] [-S] [-s] [-u] [-c CLIENT] [-v]
            [--no-deactivate] [--deploy-keys] [--debug] [--prod] [--from-prod]
            [--no-repos] [-d DATABASE] [-m MODULE] [--nginx] [-Q repo] [--backup-list]
            [--restore] [-f BACKUP_FILE] [-H] [-V] [--create-test-db] [--force-create]
            [--base-dir BASE_DIR]

    Odoo Environment Manager v0.15.1 - by jeo Software <jorge.obiols@gmail.com>

    options:
    -h, --help           show this help message and exit
    -i, --install        The first time it runs, it creates the directory structure and
                        clones all repositories declared in the project. If run again,
                        it updates the repositories. Use together with --extract-sources
                        to copy the sources from the Odoo image to the host, which is
                        essential for working in debug mode.
    -p, --pull-images    Pull Images. Download all images declared in client manifest.
    -w, --write-config   Create / Overwrite config file.
    -R, --run-env        Run postgres, wdb and aeroo images (aeroo only for old odoo
                        versions).
    -r, --run-cli        Run odoo image
    -S, --stop-env       Stop postgres, wdb and aeroo images.
    -s, --stop-cli       Stop odoo image.
    -u, --update         Updates modules in the database. With no parameters, all modules
                        are updated. Use -m modulename to update only the specified
                        module; you can also pass a list of modules separated by commas
                        (without spaces). Use -d databasename to update a database other
                        than the default database.
    -c CLIENT            Set default client name. This option is persistent
    -v, --verbose        Go verbose mode. Prints every command
    --no-deactivate      No Deactivate database before restore. WARNING this command is
                        deprecated
    --deploy-keys        Available only in production mode. It creates a pair of deploy
                        keys for each private repository found in the manifest, lists
                        the public keys for adding to the repositories.
    --debug              Set default environment mode to debug
    --prod               Set default environment mode to production
    --from-prod          Restore backup from production server. Use with --restore. it
                        needs the option 'prod_server': 'user@vps-alias' in the
                        manifestWARNING: This options may download an exact backup
                        please deactivatebefore use.You can deactivate a database
                        running odoo with those parametersodoo deactivate -d database
    --no-repos           Does not clone or pull repos when doing -i (install)
    -d DATABASE          Set default Database name.This option is persistent
    -m MODULE            Module to update. Used with -u (update) i.e. -m sale for
                        updating sale module -m all for updating all modules. NOTE: if
                        you perform -u without -m it asumes all modules
    --nginx              Add nginx to installation: Used with -i creates nginx dir with
                        config file. Used with -r starts an nginx container linked to
                        odoo.Used with -s stops nginx container. If you want to add
                        certificates review nginx.conf file located in
                        /odoo_ar/nginx/conf NOTE: This option will be deprecated in
                        thenear future
    -Q repo              Run the tests. Required parameters: -m <module name>. Optional
                        parameters: -d <database>; if omitted, the default database will
                        be used, which is the project name + _test. NOTE: The database
                        used for testing must be created with demo data and should have
                        admin/admin credentials.
    --backup-list        List all backup files available for restore
    --restore            Restores a backup. it uses last backup and restores to default
                        database. You can change the backup file to restore with -f
                        option and change database name -d option
    -f BACKUP_FILE       Filename to restore. Used with --restore. To get the name of
                        this file issue a --backup-list command.If ommited the newest
                        file will be restored
    -H, --server-help    Show odoo server help, it shows the help from the odoo
                        imagedeclared in the cliente manifest
    -V, --version        Show version number and exit.
    --create-test-db     Create database with demo data.
    --force-create       Force database creation.
    --base-dir BASE_DIR  Set default base-dir This option is persistent.


Installation
------------
    sudo pipx install odoo-env
    see proyect in https://pypi.org/project/odoo-env/

Changelog
---------
- 0.15.1  - Fix wdb image name.
- 0.15.0  - Added support for WDB 3.3.1 for Odoo versions > 17.0.
- 0.14.3  - Compatibility with python 3.11
- 0.14.2  - Fix install bug in debug mode
- 0.14.0  - Support for installation on a server with multiple private repositories.
- 0.13.2  - Correction of a paragraph with double quotes inside double quotes.
- 0.13.1  - A second configuration section is defined. The original is used when
            setting up a server, while the other, called config-local, is used
            to define the configuration for the local environment.
            This way, the server configuration file can be defined along with
            the configuration used when working in local mode.
- 0.12.6  - A bug was found when oe attempts to change permissions on the
            backup_dir folder. In some cases, this folder is an S3 or OBS bucket,
            depending on the cloud provider. In such cases, the error is caught,
            and only a warning is displayed, as changing the permissions is not
            necessary.
- 0.12.2  - Fix bug that prevented Python versions lower than 3.12.
- 0.12.1  - When the -p command is run in debug mode, it pulls the debug
            image and performs an extract-sources; in production mode, it
            pulls the production image.
- 0.12.0  - When running tests, if no database is specified, it will use the
            default database, which is the project name + test.
- 0.11.7  - FIX -i is no longer removing directory packages
- 0.11.6  - FIX --extract-sources now can remove directory packages
- 0.11.5  - FIX --from-server does not download the database
- 0.11.4  - FIX now can download repositories with submodules
- 0.11.3  - Support for submodules, oe -w can write paths for a submodule structure
- 0.10.24 - Small patch that allows to use postgres with versions greater
            than 10.
- 0.10.23 - The postgres docker image is not required anymore it is not
            necessary.
          - new longpolling port exposed if declared in manifest
          - new parameter -E to install external dependences in manifest.py
- 0.10.22 find manifest with exact name instaed of part of name.
- 0.10.21 change dbtools version to 1.3.0
- 0.10.20 fix --restore --from-server does not work when base_dir is not
          default
- 0.10.19 dbtools for postgres 14.2
- 0.10.18 ADD warning if --nginx issued and there are no nginx image on
          proyect
- 0.10.16 FIX overwrite workers in odoo.conf
- 0.10.15 base_dir parameter on oe_config.yaml
- 0.10.14 add --extract-sources option
- 0.10.13 fix -w to take into account submodules
- 0.10.12 fix -w to take into account not standard repo structure and
          odoo.conf rights
- 0.10.11 ask before overwriting local image sources
- 0.10.10 minor refactoring, improving doc
- 0.10.9 minor fixes, more documentation
- 0.10.8 improving in writing the odoo.conf
- 0.10.7 Fix bug creating odoo.conf missing data_dir in config.
- 0.10.6 Fix bug creating odoo.conf when there are no config spec is manifest
- 0.10.5 Set parameters in odoo.conf from manifest file.
- 0.10.4 IMP creation of odoo.conf improved in V11 also.
- 0.10.3 FIX nginx config now works behind port redirections
- 0.10.2 FIX collision field in manifest "license"
- 0.10.1 FIX bad filestore dir
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
- 0.0.1  Starting project
