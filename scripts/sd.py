#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
###############################################
# shortcut for sudo docker
# sudo docker $*
###############################################
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
    if params[2] == 'inside':
        try:
            print 'going inside image ' + params[3]
            params[2:3] = ['run', '-it', '--rm', '--entrypoint=/bin/bash']
        except Exception as ex:
            params = []

    return params


if __name__ == '__main__':
    params = process_input(sys.argv)
    try:
        if len(params) > 1:
            exit(subprocess.call(params))
    except Exception as ex:
        print ex
