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
