"""Crear base de datos de con datos demo"""

import os
import subprocess

from odoo_env.client import Client
from odoo_env.messages import Msg


def restore_database(cli):
    """Restaurar backup de la base"""

    command = "docker run --rm "
    command += "--network odoo-net "
    command += f"-v {cli.backup_dir}test_bkp:/backup "
    command += f"-v {cli.base_dir}data_dir/filestore:/filestore "
    command += f"--env NEW_DBNAME={cli.name}_test "
    command += "--env ZIPFILE=test.zip "
    command += "jobiols/dbtools:1.3.1 "
    subprocess.call(command, shell=True)


def create_backup_db(client):
    """Crear una base de datos vacia con datos de test"""
    Msg().err(f"Test database does not exist, create it manually {client.name}")


def create_database(_oe, client_name):
    """Crear una BD con datos demo"""

    client = Client(_oe, client_name)
    db_bkp_file = f"{client.server_backup_dir}test_bkp/test.zip"

    if _oe.force_create:
        Msg().inf("Forced database creation")
        create_backup_db(client)

    if not os.path.exists(db_bkp_file):
        Msg().inf("I can't find the backup creating database")
        create_backup_db(client)

    restore_database(client)
