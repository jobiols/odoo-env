[![Build Status](https://travis-ci.org/jobiols/odoo-env.svg?branch=master)](https://travis-ci.org/jobiols/odoo-env)
[![codecov](https://codecov.io/gh/jobiols/docker-odoo-env/branch/master/graph/badge.svg)](https://codecov.io/gh/jobiols/docker-odoo-env)

Odooenv
=======

Warning
-------
This code is not functional, and is under development (stay tuned)

Directory structure

    /odoo
    ├── nginx
    ├── odoo-9.0
    │   └── glinsar
    │       ├── config               odoo.conf
    │       ├── data_dir             filestore
    │       ├── dist_local_packages  packages from image for debug
    │       ├── dist_packages        pagkages from image for debug
    │       ├── image_repos          repos from image for debug
    │       ├── log                  odoo.log
    │       ├── postgresql           postgres database
    │       └── sources              custom sources
    └── postfix





Functionality so far
--------------------- 
    usage: oe.py [-h]
    
    ======================================================================
    Odoo Environment Manager v0.0.1 by jeo Software jorge.obiols@gmail.com
    ======================================================================
    
    optional arguments:
      -h, --help  show this help message and exit



Tool to manage docker based odoo environments

jeo Software (c) 2018 jorge.obiols@gmail.com

This code is distributed under the AGPL license

Installation
------------
    pip install docker-odoo-env
