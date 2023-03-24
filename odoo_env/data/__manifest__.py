{
    "name": "test2_client",
    "version": "9.0.3.0",
    "license": "Other OSI approved licence",
    "category": "Tools",
    "summary": "Customización Glinsar srl",
    "author": "jeo Software",
    "depends": [
        "support_branding_jeosoft",
        # modulos instalados
        "sale",
        "l10n_ar_aeroo_sale",  # ventas
        "purchase",
        "l10n_ar_aeroo_purchase",  # compras
        "account_accountant",  # permisos para contabilidad
        "l10n_ar_aeroo_stock",
        # requeridos por el cliente
        "hr_expense",
        "crm",
        "website",  # constructor de sitios web
        "project",  # project
        "product_unique",
    ],
    "data": [],
    "test": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": [],
    #
    # Here begins docker-odoo-environment manifest
    # --------------------------------------------
    # if Enterprise it installs in a different directory than community
    "odoo-license": "CE",
    # port where odoo starts serving pages
    "port": "8069",
    # manifest version
    "env-ver": "2",
    "config": [
        "workers = 5",
        "max_cron_threads = 1",
    ],
    # Note that the branch of the repo to download is taken from the
    # module version ie. 9.0
    "git-repos": [
        "https://github.com/jobiols/odoo-addons.git",
        "https://github.com/ingadhoc/odoo-argentina.git adhoc-odoo-argentina",
        "git@github.com:jobiols/cl-amic.git",
        "git@bitbucket.org:jobiols/odoo-enterprise.git",
    ],
    # Images
    "docker-images": [
        "odoo jobiols/odoo-jeo:9.0",
        "postgres postgres:11.1-alpine",
        "aeroo adhoc/aeroo",
        "nginx nginx",
    ],
}
