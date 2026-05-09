IN_CONFIG = "/opt/odoo/etc/"
IN_DATA = "/opt/odoo/data"
IN_LOG = "/var/log/odoo"
IN_CUSTOM_ADDONS = "/opt/odoo/custom-addons"
IN_EXTRA_ADDONS = "/opt/odoo/extra-addons"
IN_DIST_PACKAGES = "/usr/lib/python{}/dist-packages"
IN_DIST_LOCAL_PACKAGES = "/usr/local/lib/python{}/dist-packages"

ODOO_PYTHON_MAP: dict[int, str] = {
    14: "3.9",
    15: "3.9",
    16: "3.9",
    17: "3.10",
    18: "3.12",
}

IN_BACKUP_DIR = "/var/odoo/backups/"

# Images
DBTOOLS_IMAGE = "jobiols/dbtools:1.3.1"
WDB_IMAGE_DEFAULT = "kozea/wdb"
WDB_IMAGE_16 = "jobiols/wdb:3.3.1"
WDB_IMAGE_NEW = "jobiols/wdb:3.3.2"
