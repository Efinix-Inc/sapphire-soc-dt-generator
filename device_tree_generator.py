#!/usr/bin/python3
# SPDX-License-Identifier: MIT
#
# Copyright (C) 2025 Efinix, Inc.

import os
import sys
import argparse
from jinja2 import Environment, FileSystemLoader
from config_parser import ConfigParser
from bus_node import BusNode
from root_node import RootNode
from soc_configs import SocConfigs
from controller import Controller
from util import *

def dt_argparser():
    dt_parse = argparse.ArgumentParser(description="Device Tree Generator")
    dt_parse.add_argument("soc_configs", type=str,
                          help="path to soc.h")
    dt_parse.add_argument("board", type=str,
                          help="Provide the board name such as Ti375N1156, Ti375C529, Ti180J484, Ti60F225, T120F324")
    dt_parse.add_argument("-c", "--user-configs", action="append", type=str,
                          help="Provide the path to a user configuration JSON file to override default device properties. For example, /path/to/user-config.json.")
    dt_parse.add_argument("-d", "--dir", type=str,
                          help="Set the generated device tree output directory. Default directory is 'output'")
    dt_parse.add_argument("-g", "--debug", action="store_true", default=False,
                          help="Show debug messages.")
    dt_parse.add_argument("-m", "--machine", action="store", type=str, default="32",
                          help="Specify the machine architecture either 32-bit or 64-bit. Default is 32.")
    dt_parse.add_argument("-o", "--outfile", type=str,
                          help="Override the dtsi output filename. Default is sapphire.dtsi")
    subparsers = dt_parse.add_subparsers(title="Operating System", dest="os") # required=True)
    os_linux_parser = subparsers.add_parser("linux", help="Target Linux device tree")
    os_uboot_parser = subparsers.add_parser("uboot", help="Target U-Boot device tree")
    os_zephyr_parser = subparsers.add_parser("zephyr", help="Target Zephyr device tree")
    os_zephyr_parser.add_argument("socname", type=str,
                                  help="Custom SoC name for Zephyr SoC dtsi file.")
    os_zephyr_parser.add_argument("zephyrboard", type=str, help="Zephyr board name.")
    os_zephyr_parser.add_argument("-em", "--extmemory", action="store_true",
                                  help="Use external memory. If no external meory enabled on the SoC, internal memory will be used instead.")

    return dt_parse.parse_args()

def get_devkits(default_config):
    devkits = []
    for value in default_config["devkits"].values():
        if isinstance(value, list):
            devkits.extend(value)
    return devkits

def main():
    args = dt_argparser()
    merged_user_configs = {}
    board_name = "Development Board"

    pwd = os.path.dirname(os.path.realpath(__file__))
    env = Environment(loader=FileSystemLoader(os.path.join(pwd, "templates")))
    dtsi_template = env.get_template("soc.jinja2")
    dts_template = env.get_template("dts.jinja2")

    default_config_file = os.path.join(pwd,"config/default.json")
    default_config = read_json_file(default_config_file)
    bus_types = default_config.get("bus_types", [])
    list_ctrl = default_config.get("peripherals", [])
    supported_oses = default_config.get("supported_os", [])
    devkits = get_devkits(default_config)

    for devkit in devkits:
        if args.board in devkit.lower():
            board_name = f"{devkit} {board_name}"

    if args.os in supported_oses:
        os_name = args.os
    else:
        print(f"Error: Unsupported OS type: {args.os}. Supported types are: {', '.join(supported_oses)}")
        sys.exit(1)

    print(f"Operating system: {os_name}")

    config_file = args.soc_configs

    outfile_dtsi = args.outfile or "sapphire.dtsi"
    outfile_dts = f"{os_name}.dts"

    if args.user_configs:
        all_configs = []
        # default_config should be the first item in the list so that args.user_configs could overrides it.
        all_configs = [default_config_file] + args.user_configs
        merged_user_configs = merge_json_files(all_configs)

        list_ctrl = merged_user_configs.get("peripherals", list_ctrl)
        bus_types = merged_user_configs.get("bus_types", bus_types)

    merged_user_configs.setdefault("root", {})["os_name"] = os_name
    merged_user_configs.setdefault("root", {})["board_name"] = board_name

    if "root" not in merged_user_configs:
        merged_user_configs["root"] = {}

    if "includes" not in merged_user_configs["root"]:
        merged_user_configs["root"]["includes"] = []

    if "zephyr" in args.os:
        inc_file = f"#include <efinix/{outfile_dtsi}>"
    else:
        inc_file = f'/include/ "{outfile_dtsi}"'

    merged_user_configs["root"]["includes"].append(inc_file)

    arch = args.machine

    dt = create_device_tree(config_file, merged_user_configs, bus_types, list_ctrl, arch, args, pwd)

    if args.debug:
        save(os.path.join(pwd, "merged_user_configs.json"), merged_user_configs)
        f_configs = os.path.join(pwd, f"soc_configs_{os_name}.json")
        save(f_configs, dt)
        print(f"Save as '{f_configs}'")

    dtsi = dtsi_template.render(dt)
    dts = dts_template.render(dt)

    output_dir = args.dir or os.path.join(pwd, "output", os_name, arch)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Saving the generated '{os_name}' device tree in '{output_dir}'")
    f_dtsi = os.path.join(output_dir, outfile_dtsi)
    f_dts = os.path.join(output_dir, outfile_dts)
    save(f_dtsi, dtsi, False)
    save(f_dts, dts, False)
    print(f"dtsi: {f_dtsi}")
    print(f"dts: {f_dts}")

def create_device_tree(config_file, merged_user_configs, bus_types, list_ctrl, arch, args, pwd=""):
    dt = {}
    bus_nodes = {}
    cpu_nodes = {}
    custom_nodes = {}
    raw_configs = read_file(config_file)

    c = ConfigParser(raw_configs)
    parsed_configs = c.parse()
    soc = SocConfigs(parsed_configs)

    if args.debug:
        save(os.path.join(pwd, "parsed_configs.json"), parsed_configs)
        c.report()

    root = RootNode(parsed_configs, user_configs=merged_user_configs, arch=arch)
    root_metadata = merged_user_configs.get("root", {})
    if isinstance(root_metadata, dict):
        root_node = root.create_root_node(**root_metadata)
    else:
        root_node = root.create_root_node()

    cpu_count = soc.get_cpu_count()
    for i in range(0, cpu_count):
        cpu_node = root.create_cpu_node(label=f"cpu{i}", instance=i)
        cpu_instance = f"cpu{i}"
        cpu_nodes[cpu_instance] = cpu_node

    root_node["cpus"] = cpu_nodes
    root_node["memory"] = root.create_memory_node()

    addr_offset = True
    if "zephyr" in args.os:
        # Zephyr does not use address offset in the reg property. Thus, disable it.
        addr_offset = not ("zephyr" in args.os)

        if args.extmemory == True:
            root_node["memory"] = root.create_internal_memory_node()

    custom_nodes = root.create_custom_nodes()

    for bus in bus_types:
        num = 0
        bn = BusNode(parsed_configs, bus, list_ctrl, user_configs=merged_user_configs, arch=arch)
        bus_instances = bn.list_bus_instances()

        for bus_instance in bus_instances:
            bn.create_bus_node(bus_instance=num, header=bus_instance)
            bus_node = bn.populate_controller_instances_nodes(bus_instance=num, addr_offset=addr_offset)
            bus_nodes[bus_instance] = bus_node
            num = num + 1

    dt["root"] = root_node
    dt["custom"] = custom_nodes
    dt["buses"] = bus_nodes

    return dt


if __name__ == "__main__":
    main()
