# SPDX-License-Identifier: MIT
#
# Copyright (C) 2023 Efinix, Inc.

from core.core import *
from core.utils import *
from core.variables import *

def dt_address_cells(num):
    return "#address-cells = <{}>;".format(num)


def dt_size_cells(num):
    return "#size-cells = <{}>;".format(num)


def dt_get_clock_frequency(cfg):
    freq = get_frequency(cfg)
    return "{}".format(freq)


"""
dt_interrupt: return a string of device tree syntax of interrupt

@cfg (list): raw data of soc.h
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of device tree interrupt syntax
"""
def dt_interrupt(cfg, peripheral, is_zephyr=False):
    out = ''

    irq = get_interrupt_id(cfg, peripheral)
    if irq:
        if is_zephyr:
            out = "{0} {1}".format(irq, 1)

        else:
            out = "{}".format(irq)

    return out

"""
dt_reg: string of device tree syntax of reg

@cfg (list): raw data of soc.h
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of device tree reg syntax
"""
def dt_reg(cfg, peripheral, is_zephyr=False, root_node=None, bus=None):
    out = ''

    addr = get_peripheral_offset_address(cfg, peripheral, root_node, bus)
    size = get_size(cfg, peripheral)

    if is_zephyr:
        addr = get_peripheral_address(cfg, peripheral)

    if addr and size:
        out = "<{0} {1}>".format(addr, size)

    return out

"""
dt_reg_z_plic: string of device tree syntax of reg for zephyr plic
@cfg (list): raw data of soc.h
"""
def dt_reg_z_plic(cfg):
    out = ''

    addr = get_peripheral_address(cfg, "PLIC")

    prio = hex(int(addr,0))
    irq_en = hex(int(addr,0) + 0x2000)
    reg = hex(int(addr,0) + 0x200000)

    out = "<{0} {1}\n\t\t\t\t{2} {3}\n\t\t\t\t{4} {5}>".format(
            prio, '0x00001000', irq_en, '0x00002000', reg, '0x00010000')

    return out

"""
dt_compatible: get compatible driver for the peripheral

@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of device tree compatible syntax
"""
def dt_compatible(peripheral, controller=False, is_zephyr=False):
    out = ''
    drv = ''

    peripheral = peripheral.lower()
    driver_data = get_driver_data(controller, is_zephyr)

    if peripheral in driver_data:
        compatible = driver_data[peripheral]['compatible']
        drv = ', '.join('"{}"'.format(drv) for drv in compatible)
        out = drv.strip("\"")

    return out

"""
dt_insert_child_node: insert child node into parent node as nested dict

@parent (dict): parent dictionary of paripheral
@child (dict): child node

return: parent node with nested child node
"""
def dt_insert_child_node(parent, child):
    for key in parent:
        parent[key].update(child)

    return parent


"""
dt_insert_data: insert device tree data into current device tree node

@node (dict): device tree node of a peripheral
@new_data (dict): new data to be inserted into the node
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: device tree node
"""
def dt_insert_data(node, new_data, peripheral):
    if peripheral in node:
        node[peripheral].update(new_data)

    return node

def dt_get_driver_private_data(peripheral, controller=False, is_zephyr=False):
    priv_data = {}
    priv_data['private_data'] = get_driver_private_data(peripheral, controller, is_zephyr)

    return priv_data

"""
dt_create_parent_node: create parent node such as clock, apb, axi

@cfg (list): raw data of soc.h
@name (str): name of the parent node
@address_cell (int):
@size_cell (int):

return: parent device tree node

"""
def dt_create_parent_node(cfg, name, addr_cell, size_cell, is_zephyr=False):
    node = {
        "name": name,
        "addr_cell": addr_cell,
        "size_cell": size_cell
    }

    if not 'cpu' in name:
        compatible = dt_compatible('bus', controller=False, is_zephyr=is_zephyr)
        node['compatible'] = compatible

    node = {name: node}

    return node

def dt_create_clock_node(cfg, label):
    name = "clock"

    node = {
        "label": label,
        "name": name,
        "addr": "1",
        "reg":  "1",
        "compatible": dt_compatible("clock"),
        "clock_freq": dt_get_clock_frequency(cfg)
    }

    parent_node = dt_create_parent_node(cfg, name, 1, 0)
    parent_node = dt_insert_child_node(parent_node, node)

    return parent_node


def dt_create_interrupt_controller_node(is_zephyr=False):
    name = "interrupt-controller"
    node = {}

    compatible = dt_compatible('plic', controller=True, is_zephyr=is_zephyr)
    priv_data = get_driver_private_data('plic', controller=True, is_zephyr=is_zephyr)
    priv_data.append(compatible)

    node = {
        "name": name,
        "label": "L",
        "private_data": priv_data
    }

    node = {'intc': node}

    return node

def dt_create_cpu_node(cfg, is_zephyr=False):
    cpu_count = get_cpu_count(cfg)
    cpu_node = {
        "cpu": {
            "label": "cpus",
            "name": "cpu",
            "cores": cpu_count,
            "arch": "riscv",
            "isa": get_cpu_isa(cfg, 0),
            "tlb": True,
            "i_cache_size": get_cache_size(cfg, 0, ICACHE),
            "i_cache_sets": get_cache_way(cfg, 0, ICACHE),
            "i_cache_block_size": get_cache_block(cfg, 0),
            "d_cache_size": get_cache_size(cfg, 0, ICACHE),
            "d_cache_sets": get_cache_way(cfg, 0, ICACHE),
            "d_cache_block_size": get_cache_block(cfg, 0),
        }
    }

    cpu_type = get_property_value(cfg, "SYSTEM_HARD_RISCV_QC32", "SYSTEM_HARD_RISCV_QC32")

    if cpu_type == str(1):
        print("DEBUG: cpu is hard soc")
        cpu_node["cpu"].update({"clock_frequency": 1000000000})

    system_core = "SYSTEM_RISCV_ISA"
    mmu = get_property_value(cfg, system_core, MMU)
    if mmu:
        cpu_node["cpu"].update({"mmu_type": "riscv,sv32"})

    intc = dt_create_interrupt_controller_node(is_zephyr=is_zephyr)

    if is_zephyr:
        intc_label = "hlic"
        intc['intc'].update({"label": intc_label})

        z_cpu = {
            "tlb": False,
            "clock_frequency": True
        }
        cpu_node['cpu'].update(z_cpu)

    cpu_node['cpu'].update(intc)

    return cpu_node

"""
dt_create_memory_node: create memory node
@cfg (list): raw data of soc.h
@is_on_chip_ram (bool): enable on chip ram for zephyr setting
@is_zephyr (bool): select if targeted os is zephyr

return: a dictionary of memory node
"""
def dt_create_memory_node(cfg, is_on_chip_ram=True, is_zephyr=False):
    label = ''
    addr = ''
    size = ''
    name = 'memory'
    keyword = 'SYSTEM_DDR_BMB'

    size = get_property_value(cfg, keyword, 'SIZE ')
    if is_zephyr:
        if is_on_chip_ram:
            label = 'ram0'
            name = 'memory0'
            keyword = 'RAM_A'
            addr = get_property_value(cfg, keyword, 'CTRL ')
            size = get_property_value(cfg, keyword, 'SIZE ')

        else:
            label = 'external_ram'
            name = 'memory1'
            addr = get_property_value_match(cfg, keyword, keyword)

        size = int(size, 16) // 1024
        reg = "{0} DT_SIZE_K({1})".format(addr, size)

    else:
        conf = get_os_data()
        # addr use linux start addr
        addr = conf['memory_mapped']['uimage']
        size = hex(int(size,0) - int(addr, 0))
        reg = "{0} {1}".format(addr, size)

    mem_node = {
        "label": label,
        "name": "memory",
        "addr": addr.lstrip('0x'),
        "size": size,
        "reg": reg,
        "device_type": "memory"
    }

    mem_node = {name: mem_node}

    return mem_node

def dt_version():
    conf = load_config_file()
    version  = '{}\n\n'.format(conf['dt_version'])
    return version


def dt_model():
    conf = load_config_file()
    model = 'model = "{}";'.format(conf['model'])
    return model

def dt_create_root_node(cfg, **kwargs):
    root_node = {
        "root": {
            "version": "/dts-v1/",
            "name": "/",
            "model": kwargs['model'],
            "addr_cell": 1,
            "size_cell": 1,
            "os": kwargs['os'],
            "device_family": kwargs['device_family'],
            "board": kwargs['board'],
            "soc_name": kwargs['soc_name'],
            "frequency": get_frequency(cfg)
        }
    }

    return root_node

"""
dt_get_bus_range: get the bus address range

@cfg (list): raw data of soc.h
@bus_name (str): can be SYSTEM_BMB, SYSTEM_AXI, SYSTEM_RAM

return: string of device tree ranges property
"""
def dt_get_bus_range(cfg, bus_name):
    bus_name = check_bus_keyword(bus_name)
    addr = get_bus_address(cfg, bus_name)
    if not addr:
        print("Error: address for {} is invalid".format(bus_name))

    size = get_property_value(cfg, bus_name, "SIZE ")
    if not size:
        keyword_size = '{}_SIZE'.format(bus_name)
        print("Error: size for {0} is invalid. Expecting {1}".format(bus_name, keyword_size))
        sys.exit(1)

    ranges = "0x0 {0} {1}".format(addr, size)
    return ranges


def dt_create_bus_node(cfg, bus_name, bus_label, is_zephyr=False):
    bus_range = ''
    label = bus_label
    bus_node = dt_create_parent_node(cfg, bus_label, 1, 1, is_zephyr=is_zephyr)

    if is_zephyr:
        label = 'soc'
        bus_label = 'bmb'
    else:
        bus_range = dt_get_bus_range(cfg, bus_label)

    addr = get_bus_address(cfg, bus_label).lstrip('0x')

    bus = {
        "name": bus_name,
        "addr": addr,
        "ranges": bus_range,
        "label": label,
        "peripherals": {}
    }

    node_header = get_node_header(bus)
    bus['header'] = node_header
    bus_node[label].update(bus)

    return bus_node
