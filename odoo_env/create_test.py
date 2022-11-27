# Crear una base de datos de test
# verificar si existe un archivo /backup_dir/test_db/[client]_test.zip
# si existe restaurarlo
# si no existe crear la BD de test hacerle backup y ponerlo ahi.

from os import path, makedirs
from odoo_env.odooenv import OdooEnv
from odoo_env.client import Client
import docker
from odoo_env.messages import Msg
import requests

msg = Msg()

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
        # verificar que tengo la base de datos y odoo
        client = docker.from_env()
        db_on = list(filter(lambda x:x.attrs['Name'].find('pg-'+cli.name)>0 ,client.containers.list()))
        odoo_on = list(filter(lambda x:x.attrs['Name'] == '/'+cli.name ,client.containers.list()))
        if not (db_on and odoo_on):
            msg.err('Odoo and Database containers must be on.')

        # verificar que no exista la base de datos {client.name}_test o sea borrarla
        url = 'http://localhost:8069/web/database/drop?master_pwd=admin&name=%s'
        url = url % (cli.name+'_test')
        answ = requests.post(url)

        # lanzar el request para crear la bdd
        url = 'http://localhost:8069/web/database/create?master_pwd=admin&name=%s&password=admin&lang=en_US&login=admin&demo=1&country_code=""&phone=""'
        url = url % (cli.name+'_test')
        answ = requests.post(url)

        # Hacer backup de la base de datos
        url = 'http://localhost:8069/web/database/backup?master_pwd=admin&name=%s'
        url = url % (cli.name + '_test')
        answ = requests.post(url)

        # escribir el backup
        if not path.exists(path.dirname(filename)):
            makedirs(path.dirname(filename))


        Aca no se donde deja el backup.... 

        with open(filename,'wb') as backup:
            backup.write(answ.text)

# sudo docker run --rm -it \
#     -v $BASE/config:/opt/odoo/etc/ \
#     -v $BASE/data_dir:/opt/odoo/data \
#     -v $BASE/sources:/opt/odoo/custom-addons \
#    --link pg-danone:db \
#    jobiols/odoo-ent:14.0e -- --stop-after-init -d [cliente]_test \
#    -i dan_website_delivery_date
