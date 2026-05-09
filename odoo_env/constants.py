from typing import NamedTuple

IN_CONFIG = "/opt/odoo/etc/"
IN_DATA = "/opt/odoo/data"
IN_LOG = "/var/log/odoo"
IN_CUSTOM_ADDONS = "/opt/odoo/custom-addons"
IN_EXTRA_ADDONS = "/opt/odoo/extra-addons"
IN_DIST_PACKAGES = "/usr/lib/python{}/dist-packages"
IN_DIST_LOCAL_PACKAGES = "/usr/local/lib/python{}/dist-packages"


class OdooVersionInfo(NamedTuple):
    python: str
    src: str
    lib: str


ODOO_VERSION_MAP: dict[int, OdooVersionInfo] = {
    14: OdooVersionInfo(
        python="3.9",
        src="/usr/lib/python3/dist-packages/odoo",
        lib="/usr/local/lib/python3.9/dist-packages",
    ),
    15: OdooVersionInfo(
        python="3.9",
        src="/usr/lib/python3/dist-packages/odoo",
        lib="/usr/local/lib/python3.9/dist-packages",
    ),
    16: OdooVersionInfo(
        python="3.9",
        src="/usr/lib/python3/dist-packages/odoo",
        lib="/usr/local/lib/python3.9/dist-packages",
    ),
    17: OdooVersionInfo(
        python="3.10",
        src="/usr/lib/python3/dist-packages/odoo",
        lib="/usr/local/lib/python3.10/dist-packages",
    ),
    18: OdooVersionInfo(
        python="3.12",
        src="/usr/lib/python3/dist-packages/odoo",
        lib="/usr/local/lib/python3.12/dist-packages",
    ),
}

IN_BACKUP_DIR = "/var/odoo/backups/"

# Images
DBTOOLS_IMAGE = "jobiols/dbtools:1.3.1"
WDB_IMAGE_DEFAULT = "kozea/wdb"
WDB_IMAGE_16 = "jobiols/wdb:3.3.1"
WDB_IMAGE_NEW = "jobiols/wdb:3.3.2"
