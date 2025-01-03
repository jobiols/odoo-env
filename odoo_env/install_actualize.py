import ast

import requests

from odoo_env.messages import Msg

msg = Msg()


def get_default_branch(repo_url):
    # Extraer el nombre de usuario y el repositorio de la URL
    repo_name = repo_url.split("github.com/")[1]
    api_url = f"https://api.github.com/repos/{repo_name}"

    # Hacer una solicitud GET para obtener la información del repositorio
    response = requests.get(api_url)
    if response.status_code != 200:
        msg.err(
            f"Error {response.status_code}: Failed to retrieve repository "
            "information."
        )

    data = response.json()
    return data.get("default_branch", False)


def download_manifest_from_github(args):
    """Si no se pasa una rama, obtener la rama predeterminada"""

    repo_url = args.install
    branch = args.branch
    name = args.client[0]

    if not branch:
        branch = get_default_branch(repo_url)
        if not branch:
            msg.err(
                "Error: We couldn't find the default branch in this "
                "repository. HINT: use -b branch."
            )

    # Obtener el contenido del archivo usando la API de GitHub
    middle = repo_url.split("github.com/")[1]
    middle = middle[:-4]
    site = "https://raw.githubusercontent.com"
    api_url = f"{site}/{middle}/refs/heads/{branch}/{name}_default/__manifest__.py"
    response = requests.get(api_url)

    # Verificar que la petición fue exitosa
    if response.status_code != 200:
        msg.err(f"Error {response.status_code}: Can not get project.")

    # leer el contenido en un diccionario
    try:
        manifest = ast.literal_eval(response.text)
    except Exception as e:
        msg.err(f"Error in project manifest: {e}")
    return manifest


# def install(args, options):
#     msg.inf(f"Installing {args.install}")

#     with tempfile.TemporaryDirectory() as temp:
#         download_manifest_from_github(args)

#     exit()


# def actualize(args, options, client_name):
#     msg.inf(f"Actualizing {client_name}")
#     exit()
