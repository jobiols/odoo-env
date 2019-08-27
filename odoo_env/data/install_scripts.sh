#!/usr/bin/env bash

# update && upgrade system
echo
echo "upgrade system"
sudo apt update && sudo apt upgrade -y

# verificar si esta python 3 instalado
python3 -V

# si no esta instalado instalar python 3
# echo
echo "installing python"
sudo apt install python3 -y

# instalar distutils
sudo apt install python3-distutils

# install pip
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

# test pip
pip -V

# install sd and oe
echo
echo "installing oe"
sudo pip install odoo-env

# install docker
echo
echo "installing docker"
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# install composer
# Run this command to download the current stable release of Docker Compose:
sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

#  Apply executable permissions to the binary:
sudo chmod +x /usr/local/bin/docker-compose

# test
docker-compose --version