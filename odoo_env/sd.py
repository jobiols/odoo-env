#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
###############################################
# shortcut for sudo docker
# sudo docker $*
###############################################
from __future__ import print_function

import subprocess
import sys


def process_input(params):
    # si no tiene parametros termino
    if len(params) <= 1:
        return []

    # el primer elemento es el nombre de este archivo, lo saco
    params.pop(0)

    # agregamos sudo docker al principio
    params[0:0] = ['sudo', 'docker']

    # pseudo sintaxis

    if params[2] == '-h':
        print('Help for sd')
        print('sd               - short for sudo docker')
        print('sd inside image  - open console inside image')
        print('sd rmall         - remove all images in memory')
        print('sd rmdiskall     - remove all images in disk')
        print('sd rmuntag       - remove all untagged images in disk')
        print('sd attach name   - attach to a running container by name')
        print(' ')
        exit()

    if params[2] == 'inside':
        try:
            print('going inside image ' + params[3])
            params[2:3] = ['run', '-it', '--rm', '--entrypoint=/bin/bash']
        except Exception:
            params = []

    if params[2] == 'rmall':
        try:
            print('removing all images in memory')
            params[2:3] = ['rm', '-f', '$(sudo docker ps -a -q)']
        except Exception:
            params = []

    if params[2] == 'rmdiskall':
        try:
            print('removing all images in disk')
            params[2:3] = ['rmi', '$(sudo docker images -q)']
        except Exception:
            params = []

    if params[2] == 'rmuntag':
        try:
            print('removing all untagged images in disk')
            cmd = '$(sudo docker images | grep "^<none>" | awk "{print $3}")'
            params[2:3] = ['rmi', cmd]
        except Exception:
            params = []

    if params[2] == 'attach':
        try:
            container_name = params[3]
            print('attaching to ' + container_name)

            # sd exec -it mario bash

            params[2:3] = ['exec', '-it']
            params[4:5] = [container_name, 'bash']
        except Exception:
            params = []

    params = ' '.join(params)
    return params


def main():
    params = process_input(sys.argv)
    try:
        if len(params) > 1:
            exit(subprocess.call(params, shell=True))
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    main()
