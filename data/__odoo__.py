{
    'name': 'test_client',
    'version': '9.0.3.0',
    'license': 'Other OSI approved licence',
    'category': 'Tools',
    'summary': 'Customización Glinsar srl',
    'author': 'jeo Software',
    'depends': [
        'support_branding_jeosoft',

        # modulos instalados
        'sale', 'l10n_ar_aeroo_sale',  # ventas
        'purchase', 'l10n_ar_aeroo_purchase',  # compras
        'account_accountant',  # permisos para contabilidad
        'l10n_ar_aeroo_stock',
        # requeridos por el cliente
        'hr_expense',
        'crm',
        'website',  # constructor de sitios web
        'project',  # project
        'product_unique',
    ],

    'data': [
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [],

     'repos': [
         {'usr': 'jobiols', 'repo': 'cl-glinsar', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'odoo-addons', 'branch': '9.0'},

         {'usr': 'jobiols', 'repo': 'odoo-argentina', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-account-financial-tools', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-miscellaneous', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-account-payment', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-aeroo_reports', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-argentina-reporting', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-reporting-engine', 'branch': '9.0'},
         {'usr': 'ingadhoc', 'repo': 'argentina-sale', 'branch': '9.0'},
         {'usr': 'ingadhoc', 'repo': 'product', 'branch': '8.0'},
         {'usr': 'oca', 'repo': 'server-tools', 'branch': '9.0'},
         {'usr': 'oca', 'repo': 'partner-contact', 'branch': '9.0'},
         {'usr': 'oca', 'repo': 'reporting-engine', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'adhoc-stock', 'branch': '9.0'},
         {'usr': 'jobiols', 'repo': 'web', 'branch': '9.0'},
         {'usr': 'ingadhoc', 'repo': 'odoo-support', 'branch': '8.0'},
     ],
     'images': [
         {'name': 'aeroo', 'usr': 'jobiols', 'img': 'aeroo-docs'},
         {'name': 'odoo', 'usr': 'jobiols', 'img': 'odoo-jeo', 'ver': '9.0'},
         {'name': 'postgres', 'usr': 'postgres', 'ver': '9.5'},
         {'name': 'nginx', 'usr': 'nginx', 'ver': 'latest'}
     ]
}
