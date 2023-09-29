#!/usr/bin/python3
# SPDX-License-Identifier: MIT
#
# Copyright (C) 2023 Efinix, Inc.

import argparse
import shutil
import subprocess
import glob
import os

look_up_riscv_efx_tool_zephyr = {
    "SYSTEM_RISCV_ISA_RV32I 1" : "RISCV_ISA_RV32I",
    "SYSTEM_RISCV_ISA_EXT_M 1" : "RISCV_ISA_EXT_M",
    "SYSTEM_RISCV_ISA_EXT_A 1" : "RISCV_ISA_EXT_A",
    "SYSTEM_RISCV_ISA_EXT_C 1" : "RISCV_ISA_EXT_C",
    "SYSTEM_RISCV_ISA_EXT_ZICSR 1" : "RISCV_ISA_EXT_ZICSR",
    "SYSTEM_RISCV_ISA_EXT_ZIFENCEI 1": "RISCV_ISA_EXT_ZIFENCEI",
    "SYSTEM_RISCV_ISA_EXT_F 1" : "RISCV_ISA_EXT_F",
    "SYSTEM_RISCV_ISA_EXT_D 1" : "RISCV_ISA_EXT_D"
}

efx_soc_series = "SOC_SERIES_EFINIX_SAPPHIRE"
DEFAULT_FREQUENCY=100000000 #Default frequency should be 100MHz

parser = argparse.ArgumentParser()
parser.add_argument("soc_name", help="Name of the SOC.")
parser.add_argument("board_name", help="Name of the Board in Zephyr.")
parser.add_argument('efx_dev_board', type=str, help='development kit name such as ti60, t120')
parser.add_argument("zephyr_path", help="Path to the Zephyr project.")
parser.add_argument("soc_h_path", help="Path to the soc.h file.")
parser.add_argument('-em',"--extmemory", action="store_true", help="Select the external memory to run Zephyr app. Revert to internal memory if external memory is not enabled. ")
args = parser.parse_args()

if args.extmemory: 
    selected_memory = "ext"
else: 
    selected_memory = "int"

soc_h_path = args.soc_h_path
soc_name = args.soc_name
zephyr_path = args.zephyr_path
board_name = args.board_name
board_name += ("_" + args.efx_dev_board)
current_dir = os.path.dirname(os.path.abspath(__file__))
z_soc_soc_dir = os.path.join(zephyr_path, "dts", "riscv", "efinix")

if not os.path.isdir(zephyr_path):
    print(f"Error: The provided Zephyr path does not exist: {zephyr_path}")
    exit(1)

if not os.path.isfile(soc_h_path):
    print(f"Error: The provided soc.h path does not exist: {soc_h_path}")
    exit(1)

if (selected_memory != 'int' and selected_memory != 'ext'):
    print(f"Error: The provided memory selection not support: {selected_memory}. Supported: int, ext")
    exit(1)

# Get the SOC defines from the soc.h file
soc_defines = set()
uart_defined = False
gpio_defined = False
external_ram_defined = False
clint_freq = DEFAULT_FREQUENCY
with open(soc_h_path, 'r') as f:
    for line in f:
        if line.startswith("#define "):
            part = line.split()
            if len(part) >= 3:
                define = part[1] +" "+part[2]
            else:
                define = part[1]
            #define = line.split()[1]
            soc_defines.add(define)
            if "SYSTEM_UART_" in define:
                uart_defined = True
            if "SYSTEM_GPIO" in define:
                gpio_defined = True
            if "SYSTEM_DDR_BMB" in define: 
                external_ram_defined = True
            if "SYSTEM_CLINT_HZ" in define: 
                clint_freq = part[2] #get the CLINT frequency

# if the external ram not defined, force the selected memory to internal memory config
if (external_ram_defined == False): 
    selected_memory = 'int' 

# Open the Kconfig.soc file for writing
kconfig_soc_path = os.path.join(zephyr_path, "soc/riscv/riscv-privilege/efinix-sapphire/Kconfig.soc")
with open(kconfig_soc_path, 'r') as f:
    kconfig_soc_lines = f.readlines()

    #read line and check if the soc is already defined
    for line in kconfig_soc_lines:
        if line.startswith("config SOC_RISCV32_EFINIX_SAPPHIRE_"):
            if soc_name.upper() in line:
                print("Error: SOC already defined in Kconfig.soc. Path: {}".format(kconfig_soc_path))
                exit(1)

new_config = f"\nconfig SOC_RISCV32_EFINIX_SAPPHIRE_{soc_name.upper()}\n"
new_config += f"\tbool \"Efinix Sapphire VexRiscv system implementation for {soc_name}\"\n"
new_config += "\tselect INCLUDE_RESET_VECTOR\n"

for key, val in look_up_riscv_efx_tool_zephyr.items():
    if key in soc_defines:
        new_config += f"\tselect {val}\n"
if "SYSTEM_RISCV_ISA_EXT_A 1" in soc_defines:
    new_config += "\tselect ATOMIC_OPERATIONS_BUILTIN\n"

# Remove the 'endchoice' from the last config
kconfig_soc_lines[-1] = kconfig_soc_lines[-1].replace("endchoice", "")

# Append the new config
kconfig_soc_lines.append(new_config)
kconfig_soc_lines.append("endchoice\n")

# Write the updated Kconfig.soc back to the file
with open(kconfig_soc_path, 'w') as f:
    f.writelines(kconfig_soc_lines)
    print("Info: Kconfig.soc updated. Path: {}".format(kconfig_soc_path))

if os.path.exists(os.path.join(zephyr_path, "boards/riscv", board_name)):
    print("Error: Board already exists. Path: {}".format(os.path.join(zephyr_path, "boards/riscv", board_name)))
    exit(1)
# Create board directory
z_board_dir = os.path.join(zephyr_path, "boards/riscv", board_name)
os.makedirs(z_board_dir, exist_ok=True)


# Create {board's name}_defconfig
defconfig_path = os.path.join(z_board_dir, f"{board_name}_defconfig")
with open(defconfig_path, 'w') as f:
    f.write("CONFIG_{}=y\n".format(efx_soc_series))
    f.write(f"CONFIG_SOC_RISCV32_EFINIX_SAPPHIRE_{soc_name.upper()}=y\n")
    f.write("CONFIG_BOARD_{}=y\n".format(board_name.upper()))
    f.write("CONFIG_CLOCK_CONTROL=n\n")
    f.write("CONFIG_XIP=n\n")
    f.write("CONFIG_HEAP_MEM_POOL_SIZE=16384\n")
    f.write("CONFIG_INIT_STACKS=n\n")
    if uart_defined:
        f.write("CONFIG_CONSOLE=y\n")
        f.write("CONFIG_SERIAL=y\n")
        f.write("CONFIG_UART_CONSOLE=y\n")
    if gpio_defined:
        f.write("CONFIG_GPIO=y\n")
    f.write("CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC="+clint_freq+"\n")
    print("Info: {}_defconfig file created. Path: {}".format(board_name,defconfig_path))

# Create Kconfig.board
kconfig_board_path = os.path.join(z_board_dir, "Kconfig.board")
with open(kconfig_board_path, 'w') as f:
    f.write("config BOARD_{}\n".format(board_name.upper()))
    f.write("\tbool \"Board with Efinix Sapphire riscv with custom SoC: {}\"\n".format(soc_name))
    f.write("\tdepends on {}\n".format(efx_soc_series)) 
    print("Info: Kconfig.board file created. Path: {}".format(kconfig_board_path))

# Create Kconfig.defconfig
kconfig_defconfig_path = os.path.join(z_board_dir, "Kconfig.defconfig")
with open(kconfig_defconfig_path, 'w') as f:
    f.write("if BOARD_{}\n\n".format(board_name.upper()))
    f.write("config BOARD\n")
    f.write("\tdefault \"{}\"\n\n".format(board_name.lower()))
    f.write("endif\n")

dt_gen_script_path = os.path.join(current_dir, "device_tree_generator.py")
z_config = os.path.join(current_dir, "config/zephyr_slaves.json")

if selected_memory == "int": 
    subprocess.run(["python3", dt_gen_script_path, "-c", z_config, soc_h_path, args.efx_dev_board, "zephyr", soc_name, board_name])
else: 
    subprocess.run(["python3", dt_gen_script_path, "-c", z_config, soc_h_path, args.efx_dev_board, "zephyr", soc_name, board_name, "-em"])



gen_dts_path = os.path.join(current_dir, "dts")
#handle soc dts file
soc_dts_pattern = os.path.join(gen_dts_path, f"sapphire_soc_{soc_name}.dtsi")
matching_files = glob.glob(soc_dts_pattern)
if matching_files:
    copy_path = shutil.copy(matching_files[0], z_soc_soc_dir)
    print("Info: Found soc dtsi file {0} and copied to {1}".format(matching_files[0], copy_path))
else:
    print(f'The file {soc_dts_pattern} does not exist.')


#handle board dts file
board_dts_pattern = os.path.join(gen_dts_path, f"{board_name}.dts")
matching_files = glob.glob(board_dts_pattern)
if matching_files:
    copy_path = shutil.copy(matching_files[0], z_board_dir)
    print("Info: Found dts file {0} and copied to {1}".format(matching_files[0], copy_path))
else:
    print(f'The file {board_dts_pattern} does not exist.')

print("Info: Zephyr Board name: {}".format(board_name))
