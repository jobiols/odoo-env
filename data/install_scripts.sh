#!/usr/bin/env bash

# update system
echo
echo "upgrade system"
sudo apt-get update && sudo apt-get upgrade -y

# install sd and oe
echo
echo "installing oe"
sudo echo "~/odoo-env/scripts/oe.py \$*" > /usr/local/bin/oe
sudo chmod +x /usr/local/bin/oe
echo
echo "installing sd"
sudo cp ~/odoo-env/scripts/sd.py /usr/local/bin/sd

# install python 2.7
echo
echo "installing python"
sudo apt-get install python -y

# install docker
echo
echo "installing docker"
git clone https://github.com/docker/docker-install.git ~/temp
bash ~/temp/install.sh
rm -r /temp