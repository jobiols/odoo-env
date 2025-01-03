## THE PROJECT, where all the install information resides.

What you need to know:

1. The project is an odoo module.
1. This module has an extended manifest. Odoo does not read the extended key words, then is an installable module.
1. Odoo-env reads the manifest to know how to install the system
1. The information it holds:

        Odoo Version: The mayor version of the "version" keyword
        env-ver: The version of the extended sintax actually v2
        config: The data to write in odoo.conf
        odoo-license: EE o CE
        port: Port where odoo docker image starts serving pages.
        git-repos: list of repositories to install
        docker-images: list of docker images to pull

Additionally, as a best practice, we can place all the modules required by the
installation in the depends list, then the project not only serves to install but also to
create an empty database with all the required modules.

It is also recommended that you never install modules from the odoo interface, you can
simply add in the depends of the project and then issue a **oe -u** that magically
do an **odoo-bin --update all --stop-after-init** inside the container.
Then you have a documented list of installed modules.

## Syntax and examples
### 'git-repos':

General syntax: <repo> [<directory>[/<directory>] [-b <branch>]

The git-repos keyword is a list of all the repositories to install, in the simplest form you can list the url's of the repos this way:

```
  'git-repos': [
    'https://github.com/OCA/account-invoicing.git',
    'https://github.com/OCA/account-financial-tools.git'
  ]
```

It leads to a tree like this
```
   sources
   ├── account-financial-tools
   └── account-invoicing
```

Now if you want to add this repo:

https://github.com/ingadhoc/account-invoicing.git

it has the same name as oca repo, then you need to rename it, following the git sintax. A good practice is to rename all the repos this way:

```
  'git-repos': [
    'https://github.com/OCA/account-invoicing.git oca-account-invoicing',
    'https://github.com/OCA/account-financial-tools.git oca-account-financial-tools'
    'https://github.com/ingadhoc/account-invoicing.git adhoc-account-invoicing'
  ]
```

You get this tree
```
   sources
   ├── oca-account-financial-tools
   ├── oca-account-invoicing
   └── adhoc-account-invoicing

```

Now suppose you have to add: https://github.com/ctmil/meli_oerp.git

this is a repository that contains a single module with leads to a single level. Here we can do the following
```
  'git-repos': [
    'https://github.com/OCA/account-invoicing.git oca-account-invoicing',
    'https://github.com/OCA/account-financial-tools.git oca-account-financial-tools',
    'https://github.com/ingadhoc/account-invoicing.git adhoc-account-invoicing',
    'https://github.com/ctmil/meli_oerp.git ctmil/meli_orp'
  ]
```
You get this tree
```
   sources
   ├── oca-account-financial-tools
   ├── oca-account-invoicing
   ├── adhoc-account-invoicing
   └── ctmil
```

Inside ctmil you will find meli_orp

### What about branches
All right but which branches are you getting?. As a general rule:

**It downloads the branches whose name is te mayor version declared in the manifest**

Then if in your manifest says

        'name': 'pentecos',
        'version': '11.0.1.0.0',

Then **all the repos** will be from the branch 11.0

but you can override this, perhaps you want to get a repo that do not follow the best
practics and are in branch master, so you can write.

        'https://github.com/ctmil/odoo_barcode.git ctmil/odoo_barcode -b master'

In this case the branch to download will be main and also as the repository is not a set
of modules but **is** a module wa add ctmil/odoo_barcode so it is correctly inserted y
our sources.

## An example project:

```python
    ##############################################################################
    #
    #    Copyright (C) 2021 jeo Software  (http://www.jeosoft.com.ar)
    #    All Rights Reserved.
    #
    #    This program is free software: you can redistribute it and/or modify
    #    it under the terms of the GNU Affero General Public License as
    #    published by the Free Software Foundation, either version 3 of the
    #    License, or (at your option) any later version.
    #
    #    This program is distributed in the hope that it will be useful,
    #    but WITHOUT ANY WARRANTY; without even the implied warranty of
    #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #    GNU Affero General Public License for more details.
    #
    #    You should have received a copy of the GNU Affero General Public License
    #    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    #
    ##############################################################################

    {
        'name': 'test11',
        'version': '11.0.1.0.0',
        'category': 'Tools',
        'summary': "Test for v11 CE",
        'author': "jeo Software",
        'website': 'http://github.com/jobiols/module-repo',
        'license': 'AGPL-3',
        'depends': [
            # applications to be installed
            'sale_management',
        ],
        'installable': True,
        'application': False,

        #######################################################################
        # Here begins odoo-env manifest configuration
        #######################################################################

        # Manifest version: If omitted, version 1 is used for backward
        # compatibility. However, this will trigger a deprecation warning since
        # version 2 is now predominantly used. Support for backward compatibility
        # will be removed soon.
        'env-ver': '2',

        # ===================================================================
        # In this section, the odoo.conf file for the instance is configured.
        # There are two sections: one for local installation and another for
        # server installation, as they obviously require different parameters.
        # ===================================================================

        # in both cases the "addons path" cannot be modified; it will always be
        # overwritten by the repositories found in the sources directory.
        # "data_dir" is a fixed location inside the image

        # Local configuration applies when Odoo is in debug mode.
        'config-local': [

                # Seting an easy password for debug mode
                'admin_passwd = admin',

                # OVERIDEN PARAMETERS
                # The following parameters will be overwritten with these values:
                # "workers = 0"
                # "max_cron_threads = 0"
                # "limit_time_cpu = 0"
                # "limit_time_real = 0"
        ]

        # Production configuration applies when Odoo is in production mode.
        'config': [

            # WORKERS and MAX_CRON_WORKERS
            # If ommited it will default the calculation
            # workers = 2 per available CPU
            # max_cron_threads = 1

                    'workers = 2',
                    'max_cron_threads = 1',

            # Number of requests a worker will process before being recycled and
            # restarted. Defaults to 8192 if ommited
                    'limit_request = 8192',

            # Maximum allowed virtual memory per worker. If the limit is exceeded,
            # the worker is killed and recycled at the end of the current request.
            # Defaults to 640MB
                    'limit_memory_soft = 2147483648',

            # Hard limit on virtual memory, any worker exceeding the limit will be
            # immediately killed without waiting for the end of the current request
            # processing. Defaults to 768MB.
                    'limit_memory_hard = 2684354560',

            # Prevents the worker from using more than CPU seconds for each request.
            # If the limit is exceeded, the worker is killed. Defaults to 60 sec.
            # In DEBUG mode it is forced to Zero meaning no timeout
                    'limit_time_cpu = 60',

            # Prevents the worker from taking longer than seconds to process a request.
            # If the limit is exceeded, the worker is killed.
            # Defaults to 120.
            # Differs from --limit-time-cpu in that this is a "wall time" limit
            # including e.g. SQL queries.
            # In DEBUG mode it is forced to Zero meaning no timeout
                    'limit_time_real = 120',

            # default CSV separator for import and export
                    'csv_internal_sep = ,',

            # disable loading demo data for modules to be installed
                    'without_demo = False',

            # Comma-separated list of server-wide modules, there are modules loaded
            # automatically even if you do not create any database.
                    'server_wide_modules = base,web',

            # Filter listed database REGEXP
                    'dbfilter =',

            # Master password for database
                     'admin_passwd = my-admin-superpassword',

            # other configuration parameters
                    'db_maxconn = 64',
                    'db_name = False',
                    'db_password = odoo',
                    'db_port = 5432',
                    'db_sslmode = prefer',
                    'db_template = template0',
                    'db_user = odoo',
                    'demo = {}',
                    'email_from = False',
                    'geoip_database = /usr/share/GeoIP/GeoLite2-City.mmdb',
                    'http_enable = True',
                    'http_interface =',
                    'http_port = 8069',
                    'limit_time_real_cron = -1',
                    'list_db = True',
                    'log_db = False',
                    'log_db_level = warning',
                    'log_handler = :INFO',
                    'log_level = info',
                    'logfile = /dev/pts/0',
                    'osv_memory_age_limit = 1.0',
                    'osv_memory_count_limit = False',
                    'pg_path =',
                    'proxy_mode = False',
                    'reportgz = False',
                    'screencasts =',
                    'screenshots = /tmp/odoo_tests',
                    'smtp_password = False',
                    'smtp_port = 25',
                    'smtp_server = localhost',
                    'smtp_ssl = False',
                    'smtp_user = False',
                    'syslog = False',
                    'test_enable = False',
                    'test_file =',
                    'test_tags = None',
                    "translate_modules = ['all']",
                    'unaccent = False',
                    'upgrade_path =',
        ],

        # if ommited it defaults to CE
        'odoo-license': 'CE',

        # Production Server (change suelos13 and ec2-user for your data)
        # suelos13 is the alias you set in .ssh/config
        # i.e. you can access the server typing ssh suelos13
        # ec2-user is the user who is accessing the server, then when you perform a
        # oe --restore --from-prod
        # the backup will be transferred from server to your local with scp
        'prod_server': 'ec2-user@suelos13',

        # Port where odoo docker image starts serving pages if ommited defaults to 8069
        'port': '8069',

        # repositories to be installed in sources/
        # syntax:
        #
        #  "https://[github.com|gitlab.com|bitbucket.org/]/user/repo repo-dir -b branch"
        #  "git@[github.com|gitlab.com|bitbucket.org/]/user/repo repo-dir -b branch"
        #
        #   if branch is ommited it defaults to module name's mayor version
        #   if repo-dir if ommited it defaults to repo name
        #
        #   examples:
        #   'https://github.com/oca/web.git',
        #   'https://github.com/oca/web.git oca-web',
        #   'https://github.com/oca/web.git oca-web -b 11.0',
        #   'git@github.com/oca/web.git oca-web -b 11.0',
        #
        # note: in the last example for ssh protocol you have to use a SSH key

        # git-repos Syntax
        # <repo> [<directory>] [-b <branch>]
        'git-repos': [
            'https://github.com/jobiols/cl-test.git cl-test -b 11.0',
            'git@github.com:jobiols/odoo-uml.git -b 11.0',

            'https://github.com/jobiols/odoo-addons.git',
            'https://github.com/ingadhoc/odoo-argentina.git ingadhoc-odoo-argentina',
            'https://github.com/ingadhoc/account-financial-tools.git',
            'https://github.com/ingadhoc/account-payment.git',
            'https://github.com/ingadhoc/miscellaneous.git',
            'https://github.com/ingadhoc/argentina-reporting.git',
            'https://github.com/ingadhoc/reporting-engine.git',
            'https://github.com/ingadhoc/aeroo_reports.git',
        ],

        # Docker images to be used in this deployment
        # syntax: <image-name> <NAME[:TAG|@DIGEST]>
        'docker-images': [
            'odoo jobiols/odoo-jeo:11.0',
            'postgres postgres:10.1-alpine',
            'nginx nginx'
        ]
    }
```
