from odoo_env.config import OeConfig
from odoo_env.messages import Msg


def get_client(args):
    if args.client:
        OeConfig().save_client(args.client[0])
        return args.client[0]
    else:
        client = OeConfig().get_client()
        if client:
            return client
        else:
            Msg().err("Need -c option (client name). Process aborted")


def get_database(args):
    if args.database:
        return args.database[0]
    else:
        client = get_client(args)
        if client:
            suffix = "_test" if args.quality_assurance else "_prod"
            default_database = client + suffix
            Msg().inf(
                f"Using default database: {default_database}, use -d to "
                "specify another database."
            )
            return default_database
        else:
            Msg().err("Need -c option (client name). Process aborted")


def get_module(args):
    if args.module:
        return args.module
    else:
        Msg().inf(
            "Updating all modules. Use -m to specify single module "
            "or a comma separated list of modules."
        )
        return ["all"]


def get_backup_file(args):
    if args.backup_file:
        return args.backup_file[0]
    else:
        Msg().inf("Restoring newest LOCAL backup. Use -f to store specific one.")
        return False


def get_prod_backup_file(args):
    if args.backup_file:
        return args.backup_file[0]
    else:
        Msg().inf("Restoring newest SERVER backup. Use -f to store specific one.")
        return False


def get_param(args, param):
    if param == "client":
        return get_client(args)

    if param == "database":
        return get_database(args)

    if param == "module":
        return get_module(args)

    if param == "backup_file":
        if args.from_prod:
            return get_prod_backup_file(args)
        else:
            return get_backup_file(args)

    if param == "no-deactivate":
        if args.no_deactivate:
            return args.no_deactivate
        else:
            return False
