Install Odoo with odoo-env
==========================

#update system
sudo apt-get update && sudo apt-get upgrade -y

#install git
sudo apt-get install git

#install odoo-env
git clone https://github.com/jobiols/odoo-env.git
sudo odoo-env/data/install_scripts.sh
