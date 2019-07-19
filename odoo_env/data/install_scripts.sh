#!/usr/bin/env bash

# Make sure only root can run our script
if [[ $EUID -ne 0 ]]; then
  echo "Please run as root"
  exit 1
fi

# update && upgrade system
echo
echo "upgrade system"
apt-get update && apt-get upgrade -y

# install sd and oe
echo
echo "installing oe"
echo "~/odoo-env/scripts/oe.py \$*" > /usr/local/bin/oe
chmod +x /usr/local/bin/oe

echo
echo "installing sd"
cp ~/odoo-env/scripts/sd.py /usr/local/bin/sd

# install python 2.7
echo
echo "installing python"
apt-get install python3.6 -y

# install docker
echo
echo "installing docker"
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
