#!/usr/bin/env bash

# Generating distribution archives
# ################################

pip install --upgrade build

# ejecutar en el directorio donde esta setup.py
sudo python3 -m build
