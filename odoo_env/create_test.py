# Crear una base de datos de test
# verificar si existe un archivo /backup_dir/test_db/[client]_test.zip
# si existe restaurarlo
# si no existe crear la BD de test hacerle backup y ponerlo ahi.

from os import path
from ssl import _PasswordType
from unicodedata import name
from odoo_env.odooenv import OdooEnv
from odoo_env.client import Client


def create_test(env, client):
    cli = Client(env, client)
    filename = '%stest_db/%s_test.zip' % (cli.backup_dir, cli.name)
    if path.exists(filename):
        database = '%s_test' % client.name
        backup_file = filename
        no_deactivate = True
        from_server = False
        commands += env.restore(client.name, database,
                                backup_file, no_deactivate,
                                from_server)
    else:
        # verificar que tengo -R y -r levantados
        # mandar un POST a /web/database/create con
        # master_pwd
        # name
        # lang,
        # login,
        # password,
        # demo,

Esto crea una bd de test pero hay que borrarla primero

sudo docker run --rm -it \
    -v $BASE/config:/opt/odoo/etc/ \
    -v $BASE/data_dir:/opt/odoo/data \
    -v $BASE/sources:/opt/odoo/custom-addons \
   --link pg-danone:db \
   jobiols/odoo-ent:14.0e -- --stop-after-init -d [cliente]_test \
   -i dan_website_delivery_date
