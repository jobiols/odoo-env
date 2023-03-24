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
