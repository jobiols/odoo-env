# Documentacion de los comandos que manejan la infra local

    sudo docker network create odoo-net 2>/dev/null || true
    sudo docker run -d \
        -p 5432:5432 \
        -e POSTGRES_USER=odoo \
        -e POSTGRES_PASSWORD=odoo \
        -v /odoo/ar/odoo-14.0e/feria/postgresql/:/var/lib/postgresql/data \
        --restart=unless-stopped \
        --name pg-feria \
        --network odoo-net
        --network-alias db \
        postgres:16.10-alpine

    sudo docker run -d
        -p 1984:1984
        --name=wdb
        --restart=unless-stopped
        --network odoo-net
        kozea/wdb

    sudo docker run --rm -it
    --network odoo-net
    -p 8069:8069
    -p 8072:8072
    -v /odoo/ar/odoo-14.0e/feria/config:/opt/odoo/etc/
    -v /odoo/ar/odoo-14.0e/feria/data_dir:/opt/odoo/data
    -v /odoo/ar/odoo-14.0e/feria/log:/var/log/odoo
    -v /odoo/ar/odoo-14.0e/feria/sources:/opt/odoo/custom-addons
    -v /odoo/ar/odoo-14.0e/feria/backup_dir:/var/odoo/backups/
    -v /odoo/ar/odoo-14.0e/dist-packages:/usr/lib/python3/dist-packages
    -v /odoo/ar/odoo-14.0e/dist-local-packages:/usr/local/lib/python3.9/dist-packages/ --name feria -e ODOO_CONF=/dev/null
    -e WDB_SOCKET_SERVER=wdb
    -e WDB_NO_BROWSER_AUTO_OPEN=True
    jobiols/odoo-ent:14.0e.debug --logfile=/dev/stdout


## oe -R v16 lopez

    sudo docker network create odoo-net 2>/dev/null || true
    sudo docker run -d
        -p 5432:5432
        -e POSTGRES_USER=odoo
        -e POSTGRES_PASSWORD=odoo
        -v /odoo/ar/odoo-16.0e/lopez/postgresql/:/var/lib/postgresql/data
        --restart=unless-stopped
        --name pg-lopez
        --network odoo-net
        --network-alias db
        postgres:14.13-alpine

    sudo docker run -d
    -p 1984:1984
    --name=wdb
    --restart=unless-stopped
    --network odoo-net
    jobiols/wdb:3.3.1

    sudo docker run --rm -it
        --network odoo-net
        -p 8069:8069
        -p 8072:8072
        -v /odoo/ar/odoo-16.0e/lopez/config:/opt/odoo/etc/
        -v /odoo/ar/odoo-16.0e/lopez/data_dir:/opt/odoo/data
        -v /odoo/ar/odoo-16.0e/lopez/log:/var/log/odoo
        -v /odoo/ar/odoo-16.0e/lopez/sources:/opt/odoo/custom-addons
        -v /odoo/ar/odoo-16.0e/lopez/backup_dir:/var/odoo/backups/
        -v /odoo/ar/odoo-16.0e/dist-packages:/usr/lib/python3/dist-packages
        -v /odoo/ar/odoo-16.0e/dist-local-packages:/usr/local/lib/python3.9/dist-packages/
        --name lopez -e ODOO_CONF=/dev/null
        -e WDB_SOCKET_SERVER=wdb
        -e WDB_NO_BROWSER_AUTO_OPEN=True
        jobiols/odoo-ent:16.0e.debug --logfile=/dev/stdout

## oe v17 miltonia

### oe -R

    sudo docker network create odoo-net 2>/dev/null || true
    sudo docker run -d
    -p 5432:5432
    -e POSTGRES_USER=odoo
    -e POSTGRES_PASSWORD=odoo
    -v /odoo/ar/odoo-17.0e/miltonia/postgresql/:/var/lib/postgresql/data
    --restart=unless-stopped
    --name pg-miltonia
    --network odoo-net
    --network-alias db
    postgres:14.15-alpine

    docker run --rm \
        --network odoo-net \
        -v /odoo/ar/odoo-17.0e/miltonia/backup_dir/:/backup \
        -v /odoo/ar/odoo-17.0e/miltonia/data_dir/filestore:/filestore \
        --env NEW_DBNAME=miltonia_prod \
        jobiols/dbtools:1.3.1




### oe -r

    sudo docker run -d
    -p 1984:1984
    --name=wdb
    --restart=unless-stopped
    --network odoo-net
    jobiols/wdb:3.3.2

### oe -p

sudo docker pull jobiols/odoo-ent:17.0e.debug
sudo docker pull postgres:14.15-alpine
sudo rm -r /odoo/ar/odoo-17.0e/dist-packages
sudo rm -r /odoo/ar/odoo-17.0e/dist-local-packages
mkdir -p /odoo/ar/odoo-17.0e/dist-packages
mkdir -p /odoo/ar/odoo-17.0e/dist-local-packages
chmod og+w /odoo/ar/odoo-17.0e/dist-packages
chmod og+w /odoo/ar/odoo-17.0e/dist-local-packages
sudo docker run -it --rm --entrypoint=/extract_dist-packages.sh -v /odoo/ar/odoo-17.0e/dist-packages/:/mnt/dist-packages jobiols/odoo-ent:17.0e.debug
sudo docker run -it --rm --entrypoint=/extract_dist-local-packages.sh -v /odoo/ar/odoo-17.0e/dist-local-packages/:/mnt/dist-local-packages jobiols/odoo-ent:17.0e.debug
sudo chmod -R og+w /odoo/ar/odoo-17.0e/dist-packages/
sudo chmod -R og+w /odoo/ar/odoo-17.0e/dist-local-packages/
