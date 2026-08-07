#!/usr/bin/env python3
###############################################
# shortcut for sudo docker
###############################################
import fnmatch
import subprocess
import sys


def get_container_ids():
    """Obtiene una lista de todos los IDs de contenedores."""
    cmd = ["sudo", "docker", "ps", "-a", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("Error getting container IDs:", result.stderr)
        return []
    return result.stdout.split()


def get_image_ids():
    """Obtiene una lista de todos los IDs de imágenes."""
    cmd = ["sudo", "docker", "images", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("Error getting image IDs:", result.stderr)
        return []
    return result.stdout.split()


def get_images():
    """Obtiene una lista de tuplas (nombre, id) de todas las imágenes.

    El nombre tiene el formato repository:tag. Las imágenes sin tag
    (<none>:<none>) se devuelven igual para poder borrarlas por ID.
    """
    cmd = ["sudo", "docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.ID}}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("Error getting images:", result.stderr)
        return []
    images = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        name, _, image_id = line.rpartition(" ")
        images.append((name, image_id))
    return images


def filter_images_by_mask(images, mask):
    """Filtra imágenes cuyo nombre coincide con la máscara.

    Si la máscara no contiene metacaracteres glob (* ? [), se trata como una
    búsqueda por substring sobre el nombre completo (repository:tag), de modo
    que 'sd rmdisk debian' matchee 'debian:bullseye-slim' sin necesidad de
    comillas ni comodines.

    Si la máscara contiene metacaracteres glob, se aplica fnmatch (estilo ls)
    contra el nombre completo y contra el repository solo, de modo que
    'odoo*' matchee 'odoo:16.0'.

    Devuelve la lista de IDs a borrar.
    """
    has_glob = any(ch in mask for ch in "*?[")
    ids = []
    for name, image_id in images:
        if has_glob:
            repository = name.rsplit(":", 1)[0]
            matched = fnmatch.fnmatch(name, mask) or fnmatch.fnmatch(repository, mask)
        else:
            matched = mask in name
        if matched:
            ids.append(image_id)
    return ids


def _handle_help(_params, _base_cmd):
    print("Help for sd v2.0")
    print("sd                - short for sudo docker")
    print("sd inside <image> - open console inside an image")
    print("sd rmall          - remove all containers")
    print("sd rmdisk [mask]  - remove images from disk (forced). Plain text")
    print("                    matches as a substring (sd rmdisk debian); use")
    print("                    glob chars * ? [ for ls-style patterns. If the")
    print("                    mask is omitted, all images are removed.")
    print("sd attach <name>  - attach to a running container by name")
    print(" ")


def _handle_inside(params, base_cmd):
    if len(params) <= 1:
        return base_cmd + params
    image_name = params[1]
    print(f"Going inside image {image_name}")
    return base_cmd + ["run", "-it", "--rm", "--entrypoint=/bin/bash", image_name]


def _handle_rmall(_params, base_cmd):
    print("Removing all containers...")
    container_ids = get_container_ids()
    if not container_ids:
        print("No containers to remove.")
        return None
    return base_cmd + ["rm", "-f"] + container_ids


def _handle_rmdisk(params, base_cmd):
    if len(params) > 1:
        mask = params[1]
        print(f"Removing images matching '{mask}' from disk with force...")
        image_ids = filter_images_by_mask(get_images(), mask)
    else:
        print("Removing all images from disk with force...")
        image_ids = get_image_ids()
    if not image_ids:
        print("No images to remove.")
        return None
    return base_cmd + ["rmi", "-f"] + image_ids


def _handle_attach(params, base_cmd):
    if len(params) <= 1:
        return base_cmd + params
    container_name = params[1]
    print(f"Attaching to {container_name}")
    return base_cmd + ["exec", "-it", container_name, "bash"]


_SUBCOMMAND_HANDLERS = {
    "-h": _handle_help,
    "inside": _handle_inside,
    "rmall": _handle_rmall,
    "rmdisk": _handle_rmdisk,
    "attach": _handle_attach,
}


def process_input(params):
    # El primer elemento es el nombre de este archivo, lo saco
    params.pop(0)

    # El comando base es una lista, no una cadena
    base_cmd = ["sudo", "docker"]

    # Si no hay subcomando, no hacemos nada
    if not params:
        return None

    handler = _SUBCOMMAND_HANDLERS.get(params[0])
    if handler:
        return handler(params, base_cmd)

    # Si no es ninguno de los comandos especiales, pasamos todo a docker
    return base_cmd + params


def main():
    try:
        # process_input ahora devuelve una lista de argumentos (o None)
        final_cmd_list = process_input(sys.argv)

        if final_cmd_list:
            result = subprocess.run(final_cmd_list, check=False)
            sys.exit(result.returncode)

    except OSError as ex:
        print(f"An unexpected error occurred: {ex}")


if __name__ == "__main__":
    main()
