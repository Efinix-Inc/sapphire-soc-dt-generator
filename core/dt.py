# SPDX-License-Identifier: MIT
#
# Copyright (C) 2023 Efinix, Inc.

from core.core import *
from core.utils import *
from core.variables import *

"""
dt_compatible: get compatible driver for the peripheral

@soc_config (dict): soc configuration
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter
@controller (bool): the peripheral is controller peripheral such as plic

return: string of device tree compatible syntax
"""
def dt_compatible(soc_config, peripheral, controller=False):
    out = ''
    drv = ''

    peripheral = peripheral.lower()
    driver_data = get_driver_data(soc_config, controller)

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

def dt_get_driver_private_data(soc_config, peripheral):
    priv_data = {}
    priv_data['private_data'] = get_driver_private_data(soc_config, peripheral)

    return priv_data

def update_plic_node(soc_config, is_zephyr):
    plic_node = {}
    cpu_config = soc_config['root']['cpu']
    intc_label = cpu_config['intc']['label']
    cpu_num = cpu_config['cores']
    irq_ext = []

    driver_data = get_driver_data(soc_config)
    for i in range(cpu_num):
        l = "{0}{1}".format(intc_label, i)
        irq_e = driver_data['plic']['interrupts_extended']

        for q in irq_e:
            irq_ext.append("&{0} {1}".format(l, q))

    plic_node = {
        "interrupts_extended": irq_ext,
        "interrupts": '',
        "status": "okay"
    }

    if is_zephyr:
        node = get_peripheral_data(soc_config, PLIC)
        addr = node['addr']
        prio = hex(int(addr, 0))
        irq_en = hex(int(addr, 0) + 0x2000)
        regs = hex(int(addr,0) + 0x200000)
        reg = "<{0} {1}\n\t\t\t\t{2} {3}\n\t\t\t\t{4} {5}>".format(
                prio, '0x00001000', irq_en, '0x00002000', regs, '0x00010000')
        plic_node.update({"reg": reg})

    return plic_node

"""
dt_create_node: create a device tree node

@soc_config (dict): soc configuration after parse it
@node (dict): peripheral or bus node

return (dict): device tree node for peripherals or bus
"""
def dt_create_node(soc_config, node):
    name = ''
    is_zephyr = check_is_zephyr(soc_config)

    if 'type' in node:
        name = node['type'].lower()

    compatible = dt_compatible(soc_config, name)

    n = {
        "addr_cell": 1,
        "size_cell": 1,
        "offset": 0,
        "compatible": compatible,
        "status": "disabled"
    }
    n.update(node)

    if is_zephyr:
        if 'interrupts' in n and n['interrupts']:
            # Only take first interrupt number even though it has more than 1.
            # This is due to the zephyr gpio driver only support 1 interrupt number.
            if 'GPIO' in node['type']:
                intp = n['interrupts'].split()[0]
            else:
                intp = n['interrupts']
            n['interrupts'] = "{} 1".format(intp)

    private_data = dt_get_driver_private_data(soc_config, name)
    if private_data:
        n.update(private_data)

    if 'root' in soc_config:
        if 'plic' in name:
           plic_node = update_plic_node(soc_config, is_zephyr)
           n.update(plic_node)

        if 'clint' in name:
            n.update({"status": "okay"})

        if 'clock' in soc_config['root']:
            clock_label = soc_config['root']['clock']['label']
            clock_freq = soc_config['root']['clock']['clock_freq']
            n.update({
                "clocks": "<&{0} 0>".format(clock_label),
                "clock_freq": clock_freq
            })

    return n

"""
dt_create_peripheral_node: create the peripheral node

@soc_config (dict): soc configuration after parse it
@peripheral (str): name of the peripheral

return (dict): peripheral node
"""
def dt_create_peripheral_node(soc_config, peripheral):
    peri_node = None

    peri_node = get_peripheral_data(soc_config, peripheral)
    node = dt_create_node(soc_config, peri_node)

    return node

"""
dt_create_bus_node: create the bus node

@soc_config (dict): soc configuration after parse it
@bus (str): name of the bus such as bmb or axi

return (dict): bus node
"""
def dt_create_bus_node(soc_config, bus):
    bus_node = get_bus_data(soc_config, bus)
    node = dt_create_node(soc_config, bus_node)

    addr = bus_node['addr']
    size = bus_node['size']
    label = bus_node['label']

    if check_is_zephyr(soc_config):
        header = "soc {"
        ranges = ''
    else:
        header = "{0}: {1}@{2} {{".format(label, label, str(addr)[2:])
        ranges = "0x0 {0} {1}".format(addr, size)

    node.update({
        "peripherals": {},
        "ranges": ranges,
        "header": header
    })

    return node

"""
dt_create_parent_node: create parent node such as clock, apb, axi

@soc_config (dict): soc configuration after parse it
@name (str): name of the parent node
@address_cell (int):
@size_cell (int):

return: parent device tree node

"""
def dt_create_parent_node(soc_config, name, addr_cell, size_cell):
    node = {
        "name": name,
        "addr_cell": addr_cell,
        "size_cell": size_cell
    }

    if not 'cpu' in name:
        compatible = dt_compatible(soc_config, 'bus')
        node['compatible'] = compatible

    node = {name: node}

    return node

def dt_create_clock_node(soc_config, label):
    name = "clock"

    node = {
        "label": label,
        "name": name,
        "addr": "1",
        "reg":  "1",
        "compatible": dt_compatible(soc_config, "clock"),
        "clock_freq": soc_config['root']['cpu']['frequency']
    }

    parent_node = dt_create_parent_node(soc_config, name, 1, 0)
    parent_node = dt_insert_child_node(parent_node, node)

    return parent_node


def dt_create_interrupt_controller_node(soc_config):
    name = "interrupt-controller"
    node = {}

    compatible = dt_compatible(soc_config, 'plic', controller=True)
    priv_data = get_driver_private_data(soc_config, 'plic', controller=True)
    priv_data.append(compatible)

    node = {
        "name": name,
        "label": "L",
        "private_data": priv_data
    }

    node = {'intc': node}

    return node


def dt_create_cpu_node(soc_config):
    cpu_node = soc_config['root']['cpu']
    intc = dt_create_interrupt_controller_node(soc_config)

    if check_is_zephyr(soc_config):
        intc_label = "hlic"
        intc['intc'].update({"label": intc_label})

        z_cpu = {
            "tlb": False
        }
        cpu_node.update(z_cpu)

    cpu_node.update(intc)

    return soc_config

"""
dt_create_memory_node: create memory node
@soc_config (dict): soc configuration after parse it
@is_on_chip_ram (bool): enable on chip ram for zephyr setting

return: a dictionary of memory node
"""
def memory_node(soc_config, label, addr, size):
    if check_is_zephyr(soc_config):
        size = int(size, 16) // 1024
        reg = "{0} DT_SIZE_K({1})".format(hex(int(addr, 16)), size)

    else:
        reg = "{0} {1}".format(addr, size)

    mem_node = {
        "label": label,
        "name": "memory",
        "addr": addr.lstrip('0x'),
        "size": size,
        "reg": reg,
        "device_type": "memory"
    }

    return mem_node

def dt_create_memory_node(soc_config):
    size = 0
    addr = 0
    name = 'memory'
    label = ''
    size = soc_config['memory']['external_memory']['size']
    mem_node = {}

    if check_is_zephyr(soc_config):
        memory_types = ['external_memory', 'internal_memory']
        z_labels = ['external_ram', 'ram0']
        i = 0

        for l, t in zip(z_labels, memory_types):
            label = l
            name = 'memory{}'.format(i)
            size = soc_config['memory'][t]['size']
            addr = soc_config['memory'][t]['addr']
            mem_node[name] = memory_node(soc_config, label, addr, size)
            i += 1

    else:
        conf = get_os_data(soc_config)
        # addr use linux start addr
        addr = conf['memory_mapped']['uimage']
        size = hex(int(size, 0) - int(addr, 0))
        mem_node = memory_node(soc_config, label, addr, size)
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

def dt_create_root_node(soc_config, **kwargs):
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
            "frequency": soc_config['root']['cpu']['frequency']
        }
    }

    return root_node
