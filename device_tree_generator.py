#!/usr/bin/python3
# SPDX-License-Identifier: MIT
#
# Copyright (C) 2023 Efinix, Inc.

import argparse
import os
import sys
import shutil
import pprint
from core.core import *
from core.utils import *
from core.dt import *
from jinja2 import Environment, FileSystemLoader

pwd = os.path.dirname(os.path.realpath(__file__))
env = Environment(loader=FileSystemLoader(os.path.join(pwd, "templates")))
dtsi_template = env.get_template("soc.jinja2")
dts_template = env.get_template("dts.jinja2")

"""
update_peripheral_nodes: update the reg and offset of peripheral

The offset of a peripheral is calculate by minus the peripheral address
from the bus address. It is unknown during dt_create_peripheral_node().
This is because of the bus address is not define for the said peripheral.
We only know the bus address during connect_peripheral_to_bus(). Thus,
the offset, reg and header property get updated at very late stage.

@peripheral_node (dict): peripheral node of a device
@reg_addr (int): start address of the peripheral
@peri_size (int): size of the peripheral
@offset (int): offset of the peripheral

return (dict): updated peripheral node with offset, reg and header property
"""
def update_peripheral_nodes(peripheral_node, reg_addr, peri_size, offset):
    if 'reg' in peripheral_node and peripheral_node['reg']:
        reg = peripheral_node['reg']
    else:
        reg = "<{0} {1}>".format(reg_addr, peri_size)

    peripheral_node.update({
        "offset": offset,
        "reg": reg
    })
    header = get_node_header(peripheral_node)
    peripheral_node.update({"header": header})

    return peripheral_node

"""
connect_peripheral_to_bus: connect the peripherals to its own bus

This function create a data structure to connect the peripherals
to its own bus based on the bus address range and peripherals addresses.
This will create a complete bus architecture and the set of peripherals.

@soc_config (dict): soc configuration after parse it
@buses_node (dict): bus node
@bus (str): bus name
@bus_addr (int): start address of the @bus
@bus_range (int): range address of the @bus

return (dict): bus node with the peripherals attach to it
"""
def connect_peripheral_to_bus(soc_config, buses_node, bus, bus_addr, bus_range):
    available_peripherals = get_supported_peripherals(soc_config)
    peri_config = soc_config['peripherals']
    peripheral_node = {}

    for peripheral in available_peripherals:
        for pp in peri_config[peripheral]:
            peri_addr = peri_config[peripheral][pp]['addr']
            peri_size = peri_config[peripheral][pp]['size']
            peri_range = hex(int(peri_addr, 16) + int(peri_size, 16))

            if check_is_zephyr(soc_config):
                peripheral_node = dt_create_peripheral_node(soc_config, pp)
                peripheral_node = update_peripheral_nodes(peripheral_node, peri_addr, peri_size, peri_addr)
                buses_node[bus]['peripherals'].update({pp: peripheral_node})

            else:
                if (peri_range <= bus_range) and (bus_addr <= peri_addr):
                    offset = hex(int(peri_addr, 16) - int(bus_addr, 16))
                    peripheral_node = dt_create_peripheral_node(soc_config, pp)
                    peripheral_node = update_peripheral_nodes(peripheral_node, offset, peri_size, offset)
                    buses_node[bus]['peripherals'].update({pp: peripheral_node})

    return buses_node

def __create_bus_nodes(soc_config, buses_node, bus, bus_addr, bus_range):
    bus_node = dt_create_bus_node(soc_config, bus)
    buses_node.update({bus: bus_node})
    buses_node = connect_peripheral_to_bus(soc_config, buses_node, bus, bus_addr, bus_range)

    return buses_node

def create_bus_nodes(soc_config):
    buses_node = {}
    bus_cfg = soc_config['buses']

    if check_is_zephyr(soc_config):
        bus = 'BMB'
        buses_node = __create_bus_nodes(soc_config, buses_node, bus, '', '')

    else:
        for bus in bus_cfg:
            bus_addr = bus_cfg[bus]['addr']
            bus_size = bus_cfg[bus]['size']
            bus_range = hex(int(bus_addr, 16) + int(bus_size, 16))
            buses_node = __create_bus_nodes(soc_config, buses_node, bus, bus_addr, bus_range)

    buses_node = {"buses": buses_node}

    return buses_node

def main():

    out = ''
    board = ''
    path_dts = 'dts'
    path_dts = os.path.join(pwd, path_dts)
    dt_parse = argparse.ArgumentParser(description='Device Tree Generator')

    dt_parse.add_argument('soc', type=str, help='path to soc.h')
    dt_parse.add_argument('board', type=str, help='development kit name such as t120, ti60')
    dt_parse.add_argument('-c', '--user-config', action='append', type=str,
            help='Specify path to user configuration json file to override the APB slave device property')
    dt_parse.add_argument('-d', '--dir', type=str, help='Output generated output directory. By default is dts')
    dt_parse.add_argument('-o', '--outfile', type=str, help='Override output filename. By default is sapphire.dtsi')
    dt_parse.add_argument('-j', '--json', action='store_true', help='Save output file as json format')
    dt_parse.add_argument('-s', '--slave', action='append', type=str, help='Specify path to slave device configuration json file. This file is a slave node for the master device which appear in DTS file.')
    subparsers = dt_parse.add_subparsers(title='os', dest='os')
    os_linux_parser = subparsers.add_parser('linux', help='Target OS, Linux')
    os_zephyr_parser = subparsers.add_parser('zephyr', help='Target OS, Zephyr')
    os_zephyr_parser.add_argument('socname', type=str, help='Custom soc name for Zephyr SoC dtsi')
    os_zephyr_parser.add_argument('zephyrboard', type=str, help='Zephyr board name')
    os_zephyr_parser.add_argument('-em', '--extmemory', action="store_true", help='Use external memory. If no external memory enabled on the SoC, internal memory will be used instead.')
    args = dt_parse.parse_args()

    if args.dir:
        path_dts = args.dir

    if args.os == "zephyr":
        is_zephyr = True
    else:
        is_zephyr = False

    soc_path = args.soc
    cfg = read_file(soc_path)
    soc_config = parse_soc_config(soc_path)

    conf = load_config_file()
    device_family = ""
    devkits = conf['devkits']
    for dev_family, devs in devkits.items():
        for dev in devs:
            if args.board in dev.lower():
                board = dev
                device_family = dev_family

    if "ti375" in board.lower():
        soc_name = conf['soc_name']['hard']
    else:
        soc_name = conf['soc_name']['soft']

    if not board:
        print("Error: %s development kit is not supported\n" % args.board)
        return -1

    output_json = 'sapphire.json'
    output_filename_standalone = ""

    if is_zephyr:
        output_filename_standalone = "sapphire_soc_{soc_name}.dtsi".format(soc_name=args.socname)
        output_filename = os.path.join(path_dts, output_filename_standalone)
        dts_filename = '{}.dts'.format(args.zephyrboard)
    else:
        output_filename = 'sapphire.dtsi'
        output_filename = os.path.join(path_dts, output_filename)
        dts_filename = 'linux.dts'

    if (os.path.exists(path_dts)):
            shutil.rmtree(path_dts)

    os.makedirs(path_dts)
    dts_filename = os.path.join(path_dts, dts_filename)

    if args.outfile and not is_zephyr:
        output_filename = args.outfile

    # root
    model = conf['model']
    metadata = {
        'model': model,
        'os': args.os,
        'device_family': device_family,
        'board': board,
        'soc_name': soc_name
    }
    root_node = dt_create_root_node(cfg, **metadata)

    os_data = get_os_data(is_zephyr=is_zephyr)
    misc_node = {
            "include_headers": os_data['include_headers'],
            "chosen": os_data['chosen'],
            "aliases": os_data['aliases']
    }
    if is_zephyr:
        if not 'dts' in misc_node['include_headers']:
            misc_node['include_headers']['dts'] = {'include': []}

        misc_node['include_headers']['dts']['include'].append(
                "#include <efinix/{}>".format(output_filename_standalone))

    root_node = dt_insert_child_node(root_node, misc_node)

    memory_node = {"memory": {}}
    if is_zephyr:
        mem_node = dt_create_memory_node(cfg, False, is_zephyr)
        memory_node['memory'].update(mem_node)

    mem_node = dt_create_memory_node(cfg, True, is_zephyr)
    memory_node['memory'].update(mem_node)

    root_node = dt_insert_child_node(root_node, memory_node)

    if 'reserved_memory' in os_data:
        root_node['root']['reserved_memory'] = os_data['reserved_memory']

    if is_zephyr :
        if args.extmemory:
            root_node['root']['chosen']['private_data'].append("zephyr,sram = &external_ram;")
        else:
            root_node['root']['chosen']['private_data'].append("zephyr,sram = &ram0;")


    # cpu
    cpu_node = dt_create_cpu_node(cfg, is_zephyr)
    if cpu_node:
        root_node = dt_insert_child_node(root_node, cpu_node)

    # clock
    clk_node = dt_create_clock_node(cfg, 'apb_clock')

    if clk_node and not is_zephyr:
        root_node = dt_insert_child_node(root_node, clk_node)


    peripheral_list = get_peripherals(cfg, PERIPHERALS)

    # bus
    soc_config.update(root_node)
    buses_node = create_bus_nodes(soc_config)

    slaves_node = {}
    if args.user_config:
        for uc in args.user_config:
            if os.path.exists(uc):
                user_cfg = load_json_file(uc)
                override_peripherals(buses_node, user_cfg)

                # add child node if specify
                if 'child' in user_cfg:
                    child_node = get_child_node_header(user_cfg)
                    slaves_node = {"child": child_node['child']}
                    root_node = dt_insert_child_node(root_node, slaves_node)

                # append items into aliases or chosen node if specify
                if 'append' in user_cfg:
                    for key in user_cfg['append']:
                        if 'private_data' in root_node['root'][key]:
                            root_node['root'][key]['private_data'] += user_cfg['append'][key]
                        else:
                            root_node['root'][key]['private_data'] = user_cfg['append'][key]

            else:
                print("Error: file %s does not exists" % uc)
                sys.exit(1)

    root_node = dt_insert_child_node(root_node, buses_node)

    if args.slave:
        slaves_node = {}
        for slave_cfg in args.slave:
            if os.path.exists(slave_cfg):
                slave_node = load_json_file(slave_cfg)
                slaves_node = {**slaves_node, **slave_node['child']}

            else:
                print("Error: file %s does not exists" % slave_cfg)
                sys.exit(1)

        slaves_node = {'child': slaves_node}
        slaves_node = get_child_node_header(slaves_node)

        if not 'child' in root_node['root']:
            root_node = dt_insert_child_node(root_node, slaves_node)
        else:
            root_node['root']['child'].update(slaves_node['child'])

    out = dtsi_template.render(root_node)
    save_file(output_filename, out)
    print("Info: SoC device tree source stored in %s" % output_filename)

    # create dts file
    out = dts_template.render(root_node)
    save_file(dts_filename, out)
    print("Info: save dts of board %s in %s" % (board, dts_filename))

    # save in json format
    if args.json:
        with open(output_json, 'w') as f:
            json.dump(root_node, f, indent=4, sort_keys=False)

        print("Info: device tree json format stored in %s" % output_json)

if __name__ == "__main__":
    main()
