#!/usr/bin/env bash

# update && upgrade system
echo
echo "upgrade system"
sudo apt update && sudo apt upgrade -y

# verificar si esta python 3 instalado
python3 -V

# install python 3
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
