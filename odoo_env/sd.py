#!/usr/bin/env python3
###############################################
# shortcut for sudo docker
###############################################
import subprocess
import sys


def get_container_ids():
    """Obtiene una lista de todos los IDs de contenedores."""
    cmd = ["sudo", "docker", "ps", "-a", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error getting container IDs:", result.stderr)
        return []
    return result.stdout.split()


def get_image_ids():
    """Obtiene una lista de todos los IDs de imágenes."""
    cmd = ["sudo", "docker", "images", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error getting image IDs:", result.stderr)
        return []
    return result.stdout.split()


def process_input(params):
    # El primer elemento es el nombre de este archivo, lo saco
    params.pop(0)

    # El comando base es una lista, no una cadena
    base_cmd = ["sudo", "docker"]

    # Si no hay subcomando, no hacemos nada
    if not params:
        return None

    subcommand = params[0]

    if subcommand == "-h":
        print("Help for sd v2.0")
        print("sd               - short for sudo docker")
        print("sd inside <image> - open console inside an image")
        print("sd rmall         - remove all containers")
        print("sd rmdiskall     - remove all images from disk (forced)")
        print("sd attach <name> - attach to a running container by name")
        print(" ")
        return None  # No hay comando que ejecutar

    if subcommand == "inside" and len(params) > 1:
        image_name = params[1]
        print(f"Going inside image {image_name}")
        return base_cmd + ["run", "-it", "--rm", "--entrypoint=/bin/bash", image_name]

    if subcommand == "rmall":
        print("Removing all containers...")
        container_ids = get_container_ids()
        if not container_ids:
            print("No containers to remove.")
            return None
        return base_cmd + ["rm", "-f"] + container_ids

    if subcommand == "rmdiskall":
        print("Removing all images from disk with force...")
        image_ids = get_image_ids()
        if not image_ids:
            print("No images to remove.")
            return None
        return base_cmd + ["rmi", "-f"] + image_ids

    if subcommand == "attach" and len(params) > 1:
        container_name = params[1]
        print(f"Attaching to {container_name}")
        return base_cmd + ["exec", "-it", container_name, "bash"]

    # Si no es ninguno de los comandos especiales, simplemente pasamos todo a docker
    return base_cmd + params


def main():
    try:
        # process_input ahora devuelve una lista de argumentos (o None)
        final_cmd_list = process_input(sys.argv)

        if final_cmd_list:
            result = subprocess.run(final_cmd_list)
            sys.exit(result.returncode)

    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")


if __name__ == "__main__":
    main()
