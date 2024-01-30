# SPDX-License-Identifier: MIT
#
# Copyright (C) 2023 Efinix, Inc.

import os
import json

from core.variables import *

def read_file(filename):
    with open(filename, 'r') as f:
        cfg = f.readlines()

    return cfg


def save_file(filename, data):
    with open(filename, 'w') as f:
        f.write(data)


def load_config_file():
    with open(DRIVER_FILE, 'r') as f:
        cfg = json.load(f)

    return cfg

def load_json_file(filename):
    with open(filename, 'r') as f:
        cfg = json.load(f)

    return cfg

def print_node(node):
    print(json.dumps(node, sort_keys = False, indent = 4))

def indent(lines, level=1):
    out = ''
    ch = "\t"
    output = lines.split('\n')

    for line in output:
        out += "{0}{1}\n".format(ch*level, line)

    return out

def __dereference_symbol(cfg):
    l = []
    s = []
    v = []

    for line in cfg:
        l = line.split()
        if len(l) > 2:
            s.append(l[1])
            v.append(l[2])

    return s, v

def dereference_symbol(cfg, symbol):
    s, v = __dereference_symbol(cfg)
    i = 0
    value = 0

    for line in s:
        if symbol in line:
            value = v[i]
        i = i + 1

    return value
