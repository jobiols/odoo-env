#!/usr/bin/env python

import argparse
import sys

from odoo_env.__init__ import __version__
from odoo_env.config import OeConfig
from odoo_env.messages import OeError, msg
from odoo_env.odooenv import OdooEnv


def parse_args():

    parser = argparse.ArgumentParser(
        description=f"""
Odoo Environment Manager v{__version__} - by jeo Software <jorge.obiols@gmail.com>
"""
    )
    parser.add_argument(
        "-i",
        dest="install",
        nargs="?",
        const=True,
        metavar="REPO_URL",
        help=(
            "Install environment / update repositories. If no URL is provided, repositories are "
            "taken from the manifest. Optionally, a repository URL can be provided for the first "
            "intallation, e.g. oe -i git@github.com:org/repo.git"
        ),
    )

    parser.add_argument(
        "-R",
        dest="run_env",
        action="store_true",
        help="Run postgres, wdb and aeroo images (aeroo only for old odoo versions).",
    )

    parser.add_argument(
        "-p",
        dest="pull_images",
        action="store_true",
        help="Pull Images. Download all images declared in client manifest.",
    )

    parser.add_argument(
        "-w",
        dest="write_config",
        action="store_true",
        help="Create / Overwrite config file.",
    )

    parser.add_argument(
        "-r",
        dest="run_cli",
        action="store_true",
        help="Run odoo image",
    )

    parser.add_argument(
        "-S",
        dest="stop_env",
        action="store_true",
        help="Stop postgres, wdb and aeroo images.",
    )

    parser.add_argument(
        "-s", dest="stop_cli", action="store_true", help="Stop odoo image."
    )

    parser.add_argument(
        "-u",
        dest="update",
        action="store_true",
        help="Updates modules in the database. With no parameters, all modules "
        "are updated. Use -m list-modules to update only the specified modules "
        "Use -d databasename to update a database other than the default database.",
    )

    parser.add_argument(
        "-H",
        dest="server_help",
        action="store_true",
        help="Show odoo server help, it shows the help from the odoo image "
        "declared in the cliente manifest",
    )

    parser.add_argument(
        "-V",
        dest="version",
        action="store_true",
        help="Show version number and exit.",
    )

    parser.add_argument(
        "-Q",
        metavar="MODULES",
        dest="modules_to_test",
        help="Run the tests. Required parameters: list of modules to test separate by commas (without spaces) e.g. -Q sale,stock."
        "Optional parameters: -d <database>; if omitted, the default [project]_test database will be used, "
        "NOTE: The database used for testing must be created with demo "
        "data and must have admin/admin credentials.",
    )

    parser.add_argument(
        "-c",
        dest="client",
        help="Set default client name. This parameter is persistent",
    )

    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
        help="Go verbose mode. Prints every command",
    )

    parser.add_argument(
        "-d",
        action="store",
        dest="database",
        help="Set default Database name. This option is persistent",
    )

    parser.add_argument(
        "-m",
        action="append",
        dest="module",
        help="Module to update. Used with -u (update) i.e. -m sale for "
        "updating sale module -m all for updating all modules. NOTE: if "
        "you perform -u without -m it asumes all modules",
    )

    parser.add_argument(
        "-f",
        action="append",
        dest="backup_file",
        help="Filename to restore. Used with --restore. To get the name of "
        "If ommited the newest file will be restored",
    )

    parser.add_argument(
        "--deploy-keys",
        action="store_true",
        help="Available only in production mode. It creates a pair of deploy keys for each private "
        "repository found in the manifest, lists the public keys for adding to the repositories.",
    )

    parser.add_argument(
        "--no-deactivate",
        action="store_true",
        help="No Deactivate database before restore. WARNING this command is "
        "deprecated",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set default environment mode to debug. This parameter is persistent.",
    )

    parser.add_argument(
        "--prod",
        action="store_true",
        help="Set default environment mode to production. This parameter is persistent.",
    )

    parser.add_argument(
        "--from-prod",
        action="store_true",
        help="Restore backup from production server. Use with --restore. "
        "it needs the option 'prod_server': 'user@vps-alias' in the manifest"
        "WARNING: This options may download an exact backup please deactivate"
        "before use."
        "You can deactivate a database running odoo with those parameters"
        "odoo deactivate -d database",
    )



    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restores a backup. it uses last backup and restores to default "
        "database. You can change the backup file to restore with -f "
        "option and change database name -d option",
    )

    parser.add_argument(
        "--create-test-db",
        action="store_true",
        help="Create database with demo data.",
    )


    parser.add_argument(
        "--base-dir",
        dest="base_dir",
        help="Set the root directory where all client environments are stored "
        "(e.g. /odoo_ar/). Saved persistently in the config file; subsequent "
        "commands will use this value as the default until changed.",
    )

    return parser.parse_args()


def get_client():
    conf = OeConfig()
    client = conf.get_client()
    if not client:
        msg.err("No client configured. Use -c <client>.")
    return client


def main():
    args = parse_args()

    if args.version:
        # TODO crear un comando para esto
        msg.inf(f"oe version {__version__}")
        sys.exit()

    try:
        conf = OeConfig(args)
        conf.persist_config()
        conf.check_version()

        oe = OdooEnv(args)
        commands = oe.build_commands()
        oe.execute(commands)
    except OeError:
        sys.exit(1)


if __name__ == "__main__":
    main()
