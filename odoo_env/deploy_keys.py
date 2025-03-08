import re
import shutil
import subprocess
from pathlib import Path

from odoo_env.client import Client
from odoo_env.messages import Msg


def generate_ssh_keypair(key_name="id_ed25519", passphrase=""):
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    private_key_path = ssh_dir / key_name

    if private_key_path.exists():
        Msg().inf(f"Key '{private_key_path}' already exists.")
        return

    # Buscar la ruta absoluta de ssh-keygen
    ssh_keygen_path = shutil.which("ssh-keygen")
    if not ssh_keygen_path:
        raise FileNotFoundError("ssh-keygen not found in the system.")

    # Ejecutar ssh-keygen de manera silenciosa
    with open("/dev/null", "w") as devnull:
        subprocess.run(
            [
                ssh_keygen_path,
                "-t",
                "ed25519",
                "-f",
                str(private_key_path),
                "-N",
                passphrase,
            ],
            stdout=devnull,
            stderr=devnull,
            check=True,
        )


def update_ssh_config(key_name):
    ssh_config_path = Path.home() / ".ssh" / "config"
    host_alias = f"{key_name}.github.com"

    # Bloque a añadir (incluye salto de línea inicial para separar los bloques)
    config_entry = f"\nHost {host_alias}\n    HostName github.com\n    IdentityFile ~/.ssh/{key_name}\n    IdentitiesOnly yes\n"

    # Crear el archivo si no existe
    if not ssh_config_path.exists():
        ssh_config_path.touch(mode=0o600)

    # Leer el contenido del archivo
    with ssh_config_path.open("r") as f:
        config_content = f.read()

    # Patrón para buscar el bloque exacto del alias
    pattern = re.compile(rf"(?m)^Host {re.escape(host_alias)}\n(?:[ \t]+.*\n?)*")

    # Verificar si el alias ya existe
    if pattern.search(config_content):
        Msg().inf(f"Alias '{host_alias}' already exists in {ssh_config_path}.")
    else:
        with ssh_config_path.open("a") as f:
            f.write(config_entry)
        Msg().inf(f"Alias '{host_alias}' added to {ssh_config_path}.")


def list_public_keys(name):
    ssh_dir = Path.home() / ".ssh"
    path_key = ssh_dir / f"{name}.pub"

    Msg().inf(name)
    try:
        with path_key.open("r", encoding="utf-8") as file:
            Msg().inf(file.read())
    except Exception as ex:
        Msg().err(ex)


def deploy_keys(_oe, client_name):
    Msg().inf("Creating / Reviewing deploy keys.")
    cli = Client(_oe, client_name)

    # Detectar cuales son los repositorios que están en protocolo SSH asumiendo que son privados
    ssh_repos = []
    for repo in cli.repos:
        if repo.protocol == "ssh":
            ssh_repos.append(repo)

    # Verificar si están generadas las claves publica/privada para cada repositorio, si no están las crea
    # Editar el archivo .ssh/config para agregar los alias correspondientes si no existen
    for repo in ssh_repos:
        name = repo.code_name
        generate_ssh_keypair(name)
        update_ssh_config(name)

    # Listar las claves públicas para que las pongan en los repositorios
    Msg().inf("Available Public Keys:")
    for repo in ssh_repos:
        list_public_keys(repo.code_name)
