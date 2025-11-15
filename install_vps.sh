#!/usr/bin/env bash

# update && upgrade system
echo
echo "upgrade system"
sudo apt update && sudo apt upgrade -y

# verificar si esta python 3 instalado
python3 -V

# Verificar version de linux
lsb_release -a

# si no esta instalado instalar python 3
# echo
#echo "installing python"
#sudo apt install python3 -y

# instalar distutils
#sudo apt install python3-distutils -y en el ultimo ubuntu no tiene candidato

# install pip
# curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# sudo python3 get-pip.py
#rm get-pip.py

# install pipx
sudo apt install pipx
pipx --version

# test pip
#pip -V

# install sd and oe
pipx install ensurepath
pipx install odoo-env

set -e

# Actualizo e instalo dependencias
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Creo carpeta de keyrings
sudo install -m 0755 -d /etc/apt/keyrings

# Cargo variables del sistema
source /etc/os-release

# Determinar URL según distro
if [[ "$ID" == "debian" ]]; then
    REPO_URL="https://download.docker.com/linux/debian"
elif [[ "$ID" == "ubuntu" ]]; then
    REPO_URL="https://download.docker.com/linux/ubuntu"
else
    echo "Distribución no soportada: $ID"
    exit 1
fi

# Importar la GPG key
curl -fsSL "$REPO_URL/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Crear archivo del repo
ARCH=$(dpkg --print-architecture)

echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] $REPO_URL $VERSION_CODENAME stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Actualizar índices
sudo apt-get update

# Instalar Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Testear instalación
sudo docker run hello-world
