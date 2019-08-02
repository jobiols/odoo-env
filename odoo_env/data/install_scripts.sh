#!/usr/bin/env bash

# update && upgrade system
echo
echo "upgrade system"
sudo apt update && sudo apt upgrade -y

# install python 3.6
# echo
echo "installing python"
sudo apt install python3.6 -y

sudo apt-get install python3-distutils

# install pip
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.sh
sudo python3.6 get-pip.py
rm get-pip.sh

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
