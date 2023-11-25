#!/usr/bin/env bash

# update && upgrade system
echo
echo "upgrade system"
sudo apt update && sudo apt upgrade -y

# verificar si esta python 3 instalado
python3 -V

# si no esta instalado instalar python 3
# echo
#echo "installing python"
#sudo apt install python3 -y

# instalar distutils
sudo apt install python3-distutils -y

# install pip
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
#rm get-pip.py

# install pipx
sudo apt install pipx
pipx --version

# test pip
#pip -V

# install sd and oe
pipx install ensurepath
pipx install odoo-env

# install docker en desarrollo
echo
echo "installing docker"
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# install docker en produccion Ubuntu
# https://docs.docker.com/engine/install/ubuntu/

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install latest versin
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar docker
sudo docker run hello-world


# install composer
# Run this command to download the current stable release of Docker Compose:
sudo curl -L "https://github.com/docker/compose/releases/download/v2.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

#  Apply executable permissions to the binary:
sudo chmod +x /usr/local/bin/docker-compose

# test
docker-compose --version
