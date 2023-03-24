{
    "name": "test_client",
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
    "repos": [
        {"usr": "jobiols", "repo": "cl-test-client", "branch": "9.0"},
        {"usr": "jobiols", "repo": "odoo-addons", "branch": "9.0"},
    ],
    "docker": [
        {"name": "aeroo", "usr": "jobiols", "img": "aeroo-docs"},
        {"name": "odoo", "usr": "jobiols", "img": "odoo-jeo", "ver": "9.0"},
        {"name": "postgres", "usr": "postgres", "ver": "9.5"},
        {"name": "nginx", "usr": "nginx", "ver": "latest"},
    ],
    "port": "8069",
}
