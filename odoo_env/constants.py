from odoo_env.config import OeConfig

BASE_DIR = OeConfig().get_base_dir()
IN_CONFIG = "/opt/odoo/etc/"
IN_DATA = "/opt/odoo/data"
IN_LOG = "/var/log/odoo"
IN_CUSTOM_ADDONS = "/opt/odoo/custom-addons"
IN_EXTRA_ADDONS = "/opt/odoo/extra-addons"
IN_DIST_PACKAGES = "/usr/lib/python{}/dist-packages"
IN_DIST_LOCAL_PACKAGES = "/usr/local/lib/python{}/dist-packages"
IN_BACKUP_DIR = "/var/odoo/backups/"
WRITE_CONFIG_OLD_MODE = [8, 9, 10]

# Images
DBTOOLS_IMAGE = "jobiols/dbtools:1.3.1"
WDB_IMAGE_DEFAULT = "kozea/wdb"
WDB_IMAGE_16 = "jobiols/wdb:3.3.1"
WDB_IMAGE_NEW = "jobiols/wdb:3.3.2"
