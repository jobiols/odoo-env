""" Crear base de datos de con datos demo"""

import os
import subprocess

from odoo_env.client import Client
from odoo_env.messages import Msg


def restore_database(cli):
    """Restaurar backup de la base"""

    command = "sudo docker run --rm -i "
    command += f"--link pg-{cli.name}:db "
    command += f"-v {cli.backup_dir}test_bkp:/backup "
    command += f"-v {cli.base_dir}data_dir/filestore:/filestore "
    command += f"--env NEW_DBNAME={cli.name}_test "
    command += "--env ZIPFILE=test.zip "
    command += "jobiols/dbtools:1.3.0 "
    ret = subprocess.call(command, shell=True)


def create_backup_db(cli):
    """Crear una base de datos vacia con datos de test"""
    Msg().err("Test database does not exist, create it manually")


def create_database(_oe, client_name):
    """Crear una BD con datos demo"""

    cli = Client(_oe, client_name)
    db_bkp_file = f"{cli.server_backup_dir}test_bkp/test.zip"

    if _oe.force_create:
        Msg().inf("Forced database creation")
        create_backup_db(cli)

    if not os.path.exists(db_bkp_file):
        Msg().inf("I can't find the backup creating database")
        create_backup_db(cli)

    restore_database(cli)
