from odoo_env.config import OeConfig
from odoo_env.messages import msg


def get_client(args):
    if args.client:
        if isinstance(args.client, list):
            client = args.client[0]
        else:
            client = args.client
        OeConfig().save_client(client)
        return client
    client = OeConfig().get_client()
    if client:
        return client
    msg().err("Need -c option (client name). Process aborted")


def get_database(args):
    if args.database:
        if isinstance(args.database, list):
            return args.database[0]
        return args.database

    client = get_client(args)
    if client:
        suffix = "_test" if args.modules_to_test else "_prod"
        default_database = client + suffix
        msg.inf(
            f"Using default database: {default_database}, use -d to "
            "specify another database."
        )
        return default_database
    msg().err("Need -c option (client name). Process aborted")


def get_module(args):
    if args.module:
        return args.module
    msg.inf(
        "Updating all modules. Use -m to specify single module "
        "or a comma separated list of modules."
    )
    return ["all"]


def get_backup_file(args):
    if args.backup_file:
        if isinstance(args.backup_file, list):
            return args.backup_file[0]
        return args.backup_file

    msg.inf("Restoring newest LOCAL backup. Use -f to store specific one.")
    return False


def get_param(args, param):
    if param == "client":
        return get_client(args)

    if param == "database":
        return get_database(args)

    if param == "module":
        return get_module(args)

    if param == "backup_file":
        return get_backup_file(args)

    if param == "no-deactivate":
        if args.no_deactivate:
            return args.no_deactivate
        return False
