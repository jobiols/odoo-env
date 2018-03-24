#!/usr/bin/env bash

# install sd and oe
echo "~/odoo-env/scripts/oe.py \$*" > /usr/local/bin/oe
chmod +x /usr/local/bin/oe
cp ../scripts/sd.py /usr/local/bin/sd

# install python 2.7
apt-get install python

# install docker
git clone https://github.com/docker/docker-install.git ~/tmp
bash ~/tmp/install.sh
