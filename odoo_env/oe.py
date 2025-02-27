#!/usr/bin/env python
""" Este es el modulo principal de odoo-env """

import argparse
import sys

from odoo_env.__init__ import __version__
from odoo_env.config import OeConfig
from odoo_env.create_database import create_database
from odoo_env.deploy_keys import deploy_keys
from odoo_env.messages import Msg
from odoo_env.odooenv import OdooEnv
from odoo_env.options import get_param


def main():
    """main"""
    parser = argparse.ArgumentParser(
        description=f"""
Odoo Environment Manager v{__version__} - by jeo Software <jorge.obiols@gmail.com>
"""
    )

    parser.add_argument(
        "-i",
        "--install",
        action="store_true",
        help="The first time it runs, it creates the directory structure and "
        "clones all repositories declared in the project. If run again, it "
        "updates the repositories. Use together with --extract-sources to copy "
        "the sources from the Odoo image to the host, which is essential for "
        "working in debug mode.",
    )

    parser.add_argument(
        "-p",
        "--pull-images",
        action="store_true",
        help="Pull Images. Download all images declared in client manifest.",
    )

    parser.add_argument(
        "-w",
        "--write-config",
        action="store_true",
        help="Create / Overwrite config file.",
    )

    parser.add_argument(
        "-R",
        "--run-env",
        action="store_true",
        help="Run postgres, wdb and aeroo images (aeroo only for old odoo versions).",
    )

    parser.add_argument("-r", "--run-cli", action="store_true", help="Run odoo image")

    parser.add_argument(
        "-S",
        "--stop-env",
        action="store_true",
        help="Stop postgres, wdb and aeroo images.",
    )

    parser.add_argument(
        "-s", "--stop-cli", action="store_true", help="Stop odoo image."
    )

    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Updates modules in the database. With no parameters, all modules "
        "are updated. Use -m modulename to update only the specified module; "
        "you can also pass a list of modules separated by commas (without "
        "spaces). Use -d databasename to update a database other than the "
        "default database.",
    )

    parser.add_argument(
        "-c",
        action="append",
        dest="client",
        help="Set default client name. This option is persistent",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Go verbose mode. Prints every command",
    )

    parser.add_argument(
        "-d",
        action="store",
        nargs=1,
        dest="database",
        help="Set default Database name. This option is persistent",
    )

    parser.add_argument(
        "--no-deactivate",
        action="store_true",
        help="No Deactivate database before restore. WARNING this command is "
        "deprecated",
    )

    parser.add_argument(
        "--deploy-keys",
        action="store_true",
        help="Available only in production mode. It creates a pair of deploy keys for each private "
        "repository found in the manifest, lists the public keys for adding to the repositories.",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Set default environment mode to debug "
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Set default environment mode to production ",
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
        "--no-repos",
        action="store_true",
        help="Does not clone or pull repos when doing -i (install)",
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
        "-Q",
        action="store",
        metavar="repo",
        nargs=1,
        dest="quality_assurance",
        help="Run the tests. Required parameters: -m <module name>. Optional "
        "parameters: -d <database>; if omitted, the default database will be "
        "used, which is the project name + _test. NOTE: The database used for "
        "testing must be created with demo data and should have admin/admin "
        "credentials.",
    )

    parser.add_argument(
        "-f",
        action="append",
        dest="backup_file",
        help="Filename to restore. Used with --restore. To get the name of "
        "this file issue a --backup-list command."
        "If ommited the newest file will be restored",
    )

    parser.add_argument(
        "-H",
        "--server-help",
        action="store_true",
        help="Show odoo server help, it shows the help from the odoo image"
        "declared in the cliente manifest",
    )

    parser.add_argument(
        "-V", "--version", action="store_true", help="Show version number and exit."
    )

    parser.add_argument(
        "--nginx",
        action="store_true",
        help="Add nginx to installation: Used with -i creates nginx dir "
        "with config file. "
        "Used with -r starts an nginx container linked to odoo."
        "Used with -s stops nginx container. "
        "If you want to add certificates review nginx.conf file located "
        "in /odoo_ar/nginx/conf NOTE: This option will be deprecated in the"
        "near future",
    )

    parser.add_argument(
        "--backup-list",
        action="store_true",
        help="List all backup files available for restore",
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
        "--force-create",
        action="store_true",
        help="Force database creation.",
    )
    parser.add_argument(
        "--base-dir",
        action="append",
        dest="base_dir",
        help="Set default base-dir This option is persistent.",
    )

    args = parser.parse_args()
    if args.debug:
        OeConfig().save_environment("debug")

    if args.prod:
        OeConfig().save_environment("prod")

    if args.base_dir:
        OeConfig().save_base_dir(args.base_dir[0])

    debug_option = OeConfig().get_environment() == "debug"
    options = {
        "verbose": args.verbose,
        "debug": debug_option,
        "no-repos": args.no_repos,
        "nginx": args.nginx,
        "backup_file": args.backup_file,
        "force-create": args.force_create,
    }
    commands = []
    client_name = get_param(args, "client").strip()

    if args.server_help:
        commands += OdooEnv(options).server_help(client_name)

    if args.backup_list:
        commands += OdooEnv(options).backup_list(client_name)

    if args.restore:
        database = get_param(args, "database")
        backup_file = get_param(args, "backup_file")
        no_deactivate = args.no_deactivate
        from_server = args.from_prod
        commands += OdooEnv(options).restore(
            client_name, database, backup_file, no_deactivate, from_server
        )

    if args.install:
        commands += OdooEnv(options).install(client_name)

    if args.write_config:
        commands += OdooEnv(options).write_config(client_name)

    if args.pull_images:
        commands += OdooEnv(options).pull_images(client_name)

    if args.stop_env:
        commands += OdooEnv(options).stop_environment(client_name)

    if args.run_env:
        commands += OdooEnv(options).run_environment(client_name)

    if args.stop_cli:
        commands += OdooEnv(options).stop_client(client_name)

    if args.run_cli:
        commands += OdooEnv(options).run_client(client_name)

    if args.update:
        database = get_param(args, "database")
        modules = get_param(args, "module")
        commands += OdooEnv(options).update(client_name, database, modules)

    if args.quality_assurance:
        database = get_param(args, "database")
        commands += OdooEnv(options).qa(
            client_name, database, args.quality_assurance[0]
        )
    if args.version:
        Msg().inf(f"oe version {__version__}")
        sys.exit()

    if args.create_test_db:
        Msg().inf("Creating test database with demo data.")
        create_database(OdooEnv(options=options), client_name)
        sys.exit()

    if args.deploy_keys:
        if options["debug"]:
            Msg().err("Must be in prod mode in order to create deploy keys.")
        deploy_keys(OdooEnv(options=options), client_name)

    conf = OeConfig()

    # Verificar la version del script en pypi
    conf.check_version()

    # #####################################################################
    # ejecutar comandos
    # ######################################################################
    for command in commands:
        if command and command.check():
            Msg().inf(command.usr_msg)
            command.execute()


if __name__ == "__main__":
    main()
