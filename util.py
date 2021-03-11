#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import base64
import subprocess


def decode(base64Str):
    base64Str = base64Str.replace('\n', '').replace('-', '+').replace('_', '/')
    padding = int(len(base64Str) % 4)
    if padding != 0:
        base64Str += '=' * (4 - padding)
    return str(base64.b64decode(base64Str), 'utf-8')


def closeIptableRedirect():
    subprocess.call("iptables -t nat -F V2RAY", shell=True, stdout=subprocess.DEVNULL)
