
sudo docker run --rm -it --link wdb -p 8069:8069 -p 8072:8072
-v /odoo/ar/odoo-19.0/sulh19/config:/opt/odoo/etc/
-v /odoo/ar/odoo-19.0/sulh19/data_dir:/opt/odoo/data -v /odoo/ar/odoo-19.0/sulh19/log:/var/log/odoo
-v /odoo/ar/odoo-19.0/sulh19/sources:/opt/odoo/custom-addons
-v /odoo/ar/odoo-19.0/sulh19/backup_dir:/var/odoo/backups/

-v /odoo/ar/odoo-19.0/dist-packages:/usr/lib/python3/dist-packages
-v /odoo/ar/odoo-19.0/site-packages:/opt/venv/lib/python3.12/site-packages

--link pg-sulh19:db --name sulh19 -e ODOO_CONF=/dev/null -e WDB_SOCKET_SERVER=wdb jobiols/odoo-jeo:19.0.debug odoo-bin


ok 18
sudo docker run --rm -it --link wdb -p 8069:8069 -p 8072:8072
    -v /odoo/ar/odoo-18.0e/villandry18/config:/opt/odoo/etc/
    -v /odoo/ar/odoo-18.0e/villandry18/data_dir:/opt/odoo/data
    -v /odoo/ar/odoo-18.0e/villandry18/log:/var/log/odoo
    -v /odoo/ar/odoo-18.0e/villandry18/sources:/opt/odoo/custom-addons
    -v /odoo/ar/odoo-18.0e/villandry18/backup_dir:/var/odoo/backups/
    -v /odoo/ar/odoo-18.0e/dist-packages:/usr/lib/python3/dist-packages
    -v /odoo/ar/odoo-18.0e/dist-local-packages:/usr/local/lib/python3.12/dist-packages/
    --link pg-villandry18:db --name villandry18 -e ODOO_CONF=/dev/null -e WDB_SOCKET_SERVER=wdb jobiols/odoo-ent:18.0e.debug --logfile=/dev/stdout
