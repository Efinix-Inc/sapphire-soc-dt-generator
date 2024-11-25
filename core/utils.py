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

def find_key(nested_dict, target_key):
    if target_key in nested_dict:
        return nested_dict[target_key]

    for key, value in nested_dict.items():
        if isinstance(value, dict):
            result = find_key(value, target_key)
            if result is not None:
                return result

    return None

def update_key(nested_dict, target_key, new_value):
    if target_key in nested_dict:
        nested_dict[target_key] = new_value
        return True

    for key, value in nested_dict.items():
        if isinstance(value, dict):
            if update_key(value, target_key, new_value):
                return True

    return False

