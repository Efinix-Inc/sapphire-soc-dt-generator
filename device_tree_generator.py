#!/usr/bin/python3

import argparse
import os
import shutil
import pprint
from core.core import *
from core.utils import *
from core.dt import *

def main():

    out = ''
    board = ''
    path_dts = 'dts'
    path_dts = os.path.join(os.path.relpath(os.path.dirname(__file__)), path_dts)
    dt_parse = argparse.ArgumentParser(description='Device Tree Generator')

    dt_parse.add_argument('soc', type=str, help='path to soc.h')
    dt_parse.add_argument('board', type=str, help='development kit name such as t120, ti60')
    dt_parse.add_argument('-d', '--dir', type=str, help='Output generated output directory. By default is dts')
    dt_parse.add_argument('-o', '--outfile', type=str, help='Override output filename. By default is sapphire.dtsi')
    dt_parse.add_argument('-j', '--json', action='store_true', help='Save output file as json format')
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

    memory_selection = "ext"

    if is_zephyr :
        if not args.extmemory:
            memory_selection = "int"

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

    if is_zephyr:
        output_filename_standalone = "sapphire_soc_{soc_name}.dtsi".format(soc_name=args.socname)
        output_filename = os.path.join(path_dts, output_filename_standalone)
        dts_filename = '{}.dts'.format(args.zephyrboard)
    else:
        output_filename_standalone = ""
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
    root_node = dt_create_root_node(is_zephyr)
    root_node['root'].update(create_includes(conf, is_zephyr))

    if is_zephyr:
        root_node['root'].update(conf['zephyr_dtsi']['root'])
        ram_node = dt_create_memory_node(cfg, True, True) #onChipRAM, Zephyr
        if ram_node:
            root_node = dt_insert_child_node(root_node, ram_node)
        ext_ram_node = dt_create_memory_node(cfg, False, True) # External RAM, Zephyr
        if ext_ram_node:
            root_node = dt_insert_child_node(root_node, ext_ram_node)




    # bus
    bus_name = 'PERIPHERAL_BMB'
    bus_label = 'apbA'
    apb_node = dt_create_bus_node(cfg, bus_name, bus_label)

    if is_zephyr:
        soc_node = dt_create_soc_node(cfg)
        peripheral_parent  = soc_node
    else:
        peripheral_parent = apb_node

    # cpu
    cpu_node = dt_create_cpu_node(cfg, is_zephyr)
    if cpu_node:
        root_node = dt_insert_child_node(root_node, cpu_node)

    # clock
    clk_node = dt_create_clock_node(cfg)

    if clk_node and not is_zephyr:
        root_node = dt_insert_child_node(root_node, clk_node)

    # plic
    plic_node = dt_create_plic_node(cfg, is_zephyr=is_zephyr)
    if plic_node:
        peripheral_parent = dt_insert_child_node(peripheral_parent, plic_node)

    PERIPHERALS = ["UART", "I2C", "SPI", "GPIO"]
    #zephyr does not support i2c and spi yet
    if is_zephyr:
        PERIPHERALS = ["UART", "GPIO", "CLINT"]

    peripheral_list = get_peripherals(cfg, PERIPHERALS)
    for peripheral in peripheral_list:
        periph_node = dt_create_node(cfg, peripheral, is_zephyr)
        if periph_node:
            peripheral_parent = dt_insert_child_node(peripheral_parent, periph_node)

    root_node = dt_insert_child_node(root_node, peripheral_parent)
    out = dt_parser_nodes(root_node, root_node)
    save_file(output_filename, out)
    print("Info: SoC device tree source stored in %s" % output_filename)

    # create dts file
    dts_out = create_dts_file(cfg, peripheral_parent, memory_selection, is_zephyr, output_filename_standalone)
    save_file(dts_filename, dts_out)
    print("Info: save dts of board %s in %s" % (board, dts_filename))

    # save in json format
    if args.json:
        with open(output_json, 'w') as f:
            json.dump(root_node, f, indent=4, sort_keys=False)

        print("Info: device tree json format stored in %s" % output_json)

if __name__ == "__main__":
    main()
