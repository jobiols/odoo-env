## THE MAGIC BEGINS, From a fresh VPS to an installed odoo system

Start fresh, this example was build with Ubuntu Server 20.04 LTS

```bash
# start by upgrading the system
sudo apt update && sudo apt upgrade -y

# check if python 3 is installed
python3 -V

# if not installed do it
sudo apt install python3 -y

# install distutils
sudo apt install python3-distutils -y

# install pip
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

# test pip
pip -V

# install odoo-env
sudo pip install odoo-env

# install docker
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# install docker composer
sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
#  Apply executable permissions to the binary:
sudo chmod +x /usr/local/bin/docker-compose

# test tools
oe -h -v
sd --version
docker-compose --version
```

Ok this is all we need in the host, now begin creating a project


Enough for today stay tuned, more documentation on the way.
Jorge 2020-03-04
