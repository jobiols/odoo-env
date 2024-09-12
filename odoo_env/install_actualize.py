from odoo_env.messages import Msg
from odoo_env.odooenv import OdooEnv
import tempfile
import git

msg = Msg()

def clone_repo(repo,path):
    try:
        git.Repo.clone_from(repo,path)
    except Exception as e:
        msg.err(f'Error cloning repository: {e}')

def install_proyect(temp_path):
    # Abrir el proyecto y obtener el nombre del cliente
    env = OdooEnv


def install(args, options):
    msg.inf(f'Installing {args.install}')

    # Crear directorio temporario donde bajar el proyecto
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = temp_dir.name
    # Bajar el proyecto
    clone_repo(args.install,temp_path)

    install_proyect()

    exit()

def actualize(args, options, client_name):
    msg.inf(f'Actualizing {client_name}')
    exit()
