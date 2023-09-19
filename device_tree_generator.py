#!/usr/bin/python3

import argparse
import os
import shutil
import pprint
from core.core import *
from core.utils import *
from core.dt import *
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
dtsi_template = env.get_template("soc.jinja2")
dts_template = env.get_template("dts.jinja2")

def main():

    out = ''
    board = ''
    path_dts = 'dts'
    path_dts = os.path.join(os.path.relpath(os.path.dirname(__file__)), path_dts)
    dt_parse = argparse.ArgumentParser(description='Device Tree Generator')

    dt_parse.add_argument('soc', type=str, help='path to soc.h')
    dt_parse.add_argument('board', type=str, help='development kit name such as t120, ti60')
    dt_parse.add_argument('-b', '--bus', type=str, default="config/single_bus.json",
            help='Specify path to bus architecture for the SoC in json format. By default is "config/single_bus.json"')
    dt_parse.add_argument('-c', '--user-config', type=str,
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

    conf = load_config_file()
    devkits = conf['devkits']

    for devkit in devkits:
        devkit = devkit.lower()
        if args.board in devkit:
            board = devkit

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
    root_node = dt_create_root_node(cfg, model, args.os)

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
    buses_node = {"buses": {}}

    if is_zephyr:
        args.bus = 'config/z_single_bus.json'

    bus_cfg = load_json_file(args.bus)
    for bus in bus_cfg['buses']:
        bus_label = bus_cfg['buses'][bus]['label']

        for bus in bus_cfg['buses']:
            bus_name = bus_cfg['buses'][bus]['name']
            bus_node = dt_create_bus_node(cfg, bus_name, bus_label, is_zephyr)
            buses_node["buses"].update(bus_node)

    for bus in bus_cfg['buses']:
        for peripheral in peripheral_list:
            if peripheral.lower() in bus_cfg['buses'][bus]['peripherals']:
                periph_node = dt_create_node(cfg, root_node, peripheral, is_zephyr)
                buses_node['buses'][bus]['peripherals'].update(periph_node)

    slaves_node = {}
    if args.user_config:
        if os.path.exists(args.user_config):
            user_cfg = load_json_file(args.user_config)
            override_peripherals(buses_node, user_cfg)

            # add child node if specify
            if 'child' in user_cfg:
                child_node = get_child_node_header(user_cfg)
                slaves_node = {"child": child_node['child']}
                root_node = dt_insert_child_node(root_node, slaves_node)

    root_node = dt_insert_child_node(root_node, buses_node)

    if args.slave:
        slaves_node = {}
        for slave_cfg in args.slave:
            if os.path.exists(slave_cfg):
                slave_node = load_json_file(slave_cfg)
                slaves_node = {**slaves_node, **slave_node['child']}

        slaves_node = {'child': slaves_node}
        slaves_node = get_child_node_header(slaves_node)

        if 'child' in root_node['root']:
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
