from core.core import *
from core.utils import *
from core.variables import *

def dt_address_cells(num):
    return "#address-cells = <{}>;".format(num)


def dt_size_cells(num):
    return "#size-cells = <{}>;".format(num)


def dt_get_clock_frequency(cfg):
    freq = get_frequency(cfg)
    return "clock-frequency = <{}>;".format(freq)


def dt_get_timebase_frequency(cfg):
    freq = get_frequency(cfg)
    return "timebase-frequency = <{}>;".format(freq)


"""
dt_interrupt: return a string of device tree syntax of interrupt

@cfg (list): raw data of soc.h
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of device tree interrupt syntax
"""
def dt_interrupt(cfg, peripheral, is_zephyr=False):
    out = ''

    irq = get_interrupt_id(cfg, peripheral)
    if irq and not is_zephyr:
        out = "interrupts = <{}>;".format(irq)
    else:
        out = "interrupts = <{0} {1}>;".format(irq, 1)

    return out

"""
dt_reg: string of device tree syntax of reg

@cfg (list): raw data of soc.h
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of device tree reg syntax
"""
def dt_reg(cfg, peripheral, is_zephyr=False):
    out = ''

    addr = get_peripheral_base_address(cfg, peripheral)
    size = get_size(cfg, peripheral)

    if is_zephyr:
        addr = get_peripheral_address(cfg, peripheral)

    if addr and size:
        out = "reg = <{0} {1}>;".format(addr, size)

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

    out = "reg = <{0} {1}\n\t{2} {3}\n\t{4} {5}>;".format(prio, '0x00001000', irq_en, '0x00002000', reg, '0x00010000')

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

    drivers = load_config_file()

    if controller:
        drivers = drivers['controller']
        if is_zephyr:
            drivers = load_config_file()
            drivers = drivers['zephyr_dtsi']['controller']
    else:
        drivers = drivers['drivers']
        if is_zephyr:
            drivers = load_config_file()
            drivers = drivers['zephyr_dtsi']['drivers']

    if peripheral in drivers:
        compatible = drivers[peripheral]['compatible']
        drv = ', '.join('"{}"'.format(drv) for drv in compatible)
        out = 'compatible = {};'.format(drv)

    return out

"""
dt_get_phandle: get phandle or reference of device node label

@node (dict): device tree node
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: string of phandle for a given peripheral
"""
def dt_get_phandle(nodes, peripheral):
    phandle = ''

    if isinstance(nodes, dict):
        for key in nodes:
            if peripheral in key:
                if 'label' in nodes[key]:
                    label = nodes[peripheral]['label']
                    phandle = "&{}".format(label)
                    return phandle

            else:
                phandle = dt_get_phandle(nodes[key], peripheral)

    return phandle

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

"""
__dt_create_node_str: convert node information to string

@node (dict): node contain device tree metadata such as label, compatible, reg, interrupt
@parent_node (dict): parent of @node

return: string of device tree node
"""
def __dt_create_node_str(node, parent_node):
    out = ''
    output = ''

    if 'version' in node:
        out += node['version']

    if 'include' in node:
        for i in node['include']:
            out += "/include/ \"{}\"\n".format(i)

    if '#include' in node:
        for i in node['#include']:
            out += "#include <{}>\n".format(i)

    out += '\n'

    if 'label' in node:
        label = ''
        if not node['label'] == '':
            label = "{0}:".format(node['label'])

        if 'name' and 'addr' in node:
            out += "{0} {1}@{2} {{\n".format(label, node['name'], node['addr'])

        elif 'name' and not 'addr' in node:
            out += "{0} {1} {{\n".format(label, node['name'])

        else:
            out += "{0} {{\n".format(label)

    else:
        if 'name' and 'addr' in node:
            out += "{0}@{1} {{\n".format(node['name'], node['addr'])

        elif 'name' and not 'addr' in node:
            out += "{} {{\n".format(node['name'])

        else:
            out += ""

    if 'model' in node:
            out += "\t{}\n".format(node['model'])

    if 'device_type' in node:
            out += "\t{}\n".format(node['device_type'])

    if 'addr_cell' in node:
        #out += "\t{}\n".format(node['addr_cell'])
        addr_cell = dt_address_cells(node['addr_cell'])
        out += "\t{}\n".format(addr_cell)

    if 'size_cell' in node:
        #out += "\t{}\n".format(node['size_cell'])
        size_cell = dt_size_cells(node['size_cell'])
        out += "\t{}\n".format(size_cell)
    if 'ranges_key' in node:
        out += "\t{}\n".format(node['ranges_key'])

    if 'reg' in node:
        out += "\t{}\n".format(node['reg'])

    if 'reg-names' in node:
        out += "\t{}\n".format(node['reg-names'])

    if 'compatible' in node:
        out += "\t{}\n".format(node['compatible'])

    if 'ranges' in node:
        out += "\t{}\n".format(node['ranges'])

    # TODO: SPI does not support interrupt
    if not 'spi' in node['name']:
        if 'interrupt' in node:
            out += "\t{}\n".format(node['interrupt'])

            #phandle of interrupt-parent
            phandle = dt_get_phandle(parent_node, 'PLIC')
            if phandle:
                out += "\tinterrupt-parent = <{}>;\n".format(phandle)

    if 'isa' in node:
        out += "\t{}\n".format(node['isa'])

    if 'mmu_type' in node:
        out += "\t{}\n".format(node['mmu_type'])

    if 'icache_size' in node:
        out += "\t{}\n".format(node['icache_size'])

    if 'icache_way' in node:
        out += "\t{}\n".format(node['icache_way'])

    if 'icache_block_size' in node:
        out += "\t{}\n".format(node['icache_block_size'])

    if 'dcache_size' in node:
        out += "\t{}\n".format(node['dcache_size'])

    if 'dcache_way' in node:
        out += "\t{}\n".format(node['dcache_way'])

    if 'dcache_block_size' in node:
        out += "\t{}\n".format(node['dcache_block_size'])

    if 'tlb' in node:
        out += "\t{}\n".format(node['tlb'])
    if 'clock-frequency' in node:
        out += "\t{}\n".format(node['clock-frequency'])

    if 'private_data' in node:
        # private_data (list)
        for p in node['private_data']:
            out += "\t{}\n".format(p)

    if 'clock_cells' in node:
        out += "\t{}\n".format(node['clock_cells'])

    if 'clock_freq' in node:
        out += "\t{}\n".format(node['clock_freq'])

    if 'timebase_freq' in node:
        out += "\t{}\n".format(node['timebase_freq'])

    if 'status' in node:
        out += "\t{}\n".format(node['status'])

    return out

"""
__dt_create_node: convert node information to string

@nodes (dict): input node contain device tree metadata such as label, compatible, reg, interrupt

return: string of device tree node
"""
def __dt_create_node(nodes):
    out = ''

    parent_node = nodes;

    for node in nodes:
        out = __dt_create_node_str(node, parent_node)

    return out


def get_private_data(peripheral, controller=False, is_zephyr=False):
    priv_data = ''
    peripheral = peripheral.lower()
    drv_data = load_config_file()

    if controller:
        drv = 'controller'
        if is_zephyr:
            drv = ['zephyr_dtsi', 'controller']
    else:
        drv = 'drivers'
        if is_zephyr:
            drv = ['zephyr_dtsi', 'drivers']

    if isinstance(drv, list): # if drv is a list, then we are dealing with a nested dictionary
        if peripheral in drv_data[drv[0]][drv[1]]:
            if 'private_data' in drv_data[drv[0]][drv[1]][peripheral]:
                priv_data = drv_data[drv[0]][drv[1]][peripheral]['private_data']
    else:
        if peripheral in drv_data[drv]:
            if 'private_data' in drv_data[drv][peripheral]:
                priv_data = drv_data[drv][peripheral]['private_data']


    return priv_data



def dt_get_private_data(peripheral, controller=False, is_zephyr=False):
    priv_data = {}
    priv_data['private_data'] = get_private_data(peripheral, controller, is_zephyr)

    return priv_data

"""
dt_create_node: create a device tree node for a peripheral

@cfg (list): raw data of soc.h
@peripheral (str): peripheral name such as SPI, I2C. Must be in capital letter

return: dict of device tree peripheral nodes
"""
def dt_create_node(cfg, peripheral, is_zephyr=False):
    node = {}
    nodes = {}

    count = count_peripheral(cfg, peripheral)
    node = {"count": count}

    for i in range(0, count):
        if peripheral in CONTROLLER:
            node_idx = peripheral
            label = peripheral.lower()
            status = get_status(okay=True)
        else:
            node_idx = "{0}_{1}".format(peripheral, i)
            if not is_zephyr:
                node_label_id = chr(65+i)
            else:
                node_label_id = i
            label = "{0}{1}".format(peripheral.lower(), node_label_id)
            status = get_status(okay=False)

        reg = dt_reg(cfg, node_idx, is_zephyr)
        addr = get_peripheral_base_address(cfg, node_idx)

        if is_zephyr:
            addr = get_address(cfg, node_idx)

        node = {
            "name": peripheral.lower(),
            "label": label,
            "reg": reg,
            "addr": addr.lstrip('0x'),
            "status": status
        }

        compatible = dt_compatible(peripheral, is_zephyr=is_zephyr)
        if compatible:
            node.update({"compatible": compatible})

        irq = dt_interrupt(cfg, node_idx, is_zephyr=is_zephyr)
        if irq:
            node.update({"interrupt": irq})

        if not is_zephyr:
            clk_freq = dt_get_clock_frequency(cfg)
            if clk_freq:
                if not 'I2C' in peripheral:
                    node.update({"clock_freq": clk_freq})

        priv_data = dt_get_private_data(peripheral, is_zephyr=is_zephyr)
        if priv_data:
            node.update(priv_data)

        if  is_zephyr:
            if peripheral == PLIC:
                node.update({"reg": dt_reg_z_plic(cfg)})
                node.update({"reg-names": "reg-names = \"{0}\", \"{1}\", \"{2}\";".format('prio', 'irq_en', 'reg')})
                node.pop('interrupt')
            if peripheral == CLINT:
                node.pop('interrupt')


        nodes.update({node_idx: node})

    return nodes


def dt_create_node_str(cfg, peripheral):
    out = ''

    nodes =  dt_create_node(cfg, peripheral)
    out =  __dt_create_node(nodes)

    return out

"""
dt_create_parent_node: create parent node such as clock, apb, axi

@cfg (list): raw data of soc.h
@name (str): name of the parent node
@address_cell (int):
@size_cell (int):

return: parent device tree node

"""
def dt_create_parent_node(cfg, name, address_cell, size_cell, is_zephyr=False):
    node = {
        "name": name,
        "addr_cell": address_cell,
        "size_cell": size_cell
    }

    if not 'cpu' in name:
        compatible = dt_compatible('bus')
        node['compatible'] = compatible
        if name == 'soc':
            node['compatible'] = dt_compatible('soc', controller=True, is_zephyr=is_zephyr)

            if is_zephyr:
                node.update({'ranges_key': 'ranges;'})

    node = {name: node}

    return node

def dt_create_plic_node(cfg, is_zephyr=False):
    plic_metadata = []
    ext = ''
    node = {}
    priv_data = {}

    drivers = load_config_file()
    cpu_count = get_cpu_count(cfg)
    node = dt_create_node(cfg, PLIC, is_zephyr)

    for i in range(0, cpu_count):
        if is_zephyr:
            ext += "\n\t\t&hlic{0} 11".format(i)
            continue
        ext += "\n\t\t&L{0} 11 &L{1} 9".format(i, i)

    ext = "interrupts-extended = <{}>;".format(ext)
    priv_data = get_private_data('plic', is_zephyr=is_zephyr)
    priv_data.append(ext)
    plic_metadata = {"private_data": priv_data}
    node = dt_insert_data(node, plic_metadata, PLIC)

    return node

def dt_create_clint_node(cfg, is_zephyr=False):
    node = {}
    priv_data = {}

    node = dt_create_node(cfg, CLINT, is_zephyr)
    priv_data = get_private_data('clint', is_zephyr=is_zephyr)
    node = dt_insert_data(node, priv_data, CLINT)

    return node

def dt_create_clock_node(cfg):
    name = "clock"
    label = "apbA_clock"

    node = {
        "label": label,
        "name": name,
        "addr": "1",
        "reg": "reg = <1 0>;",
        "compatible": dt_compatible("clock"),
        "clock_cells": "#clock-cells = <0>;",
        "clock_freq": dt_get_clock_frequency(cfg)
    }

    node = {label: node}

    parent_node = dt_create_parent_node(cfg, name, 1, 0)
    parent_node = dt_insert_child_node(parent_node, node)

    return parent_node


def dt_create_interrupt_controller_node(is_zephyr=False):
    name = "interrupt-controller"
    node = {}

    compatible = dt_compatible('plic', controller=True, is_zephyr=is_zephyr)
    priv_data = get_private_data('plic', controller=True, is_zephyr=is_zephyr)
    priv_data.append(compatible)

    node = {
        "name": name,
        "private_data": priv_data
    }

    node = {name: node}

    return node

def dt_create_cpu_node(cfg, is_zephyr=False):
    name = "cpus"
    cpu_nodes = {}
    cpu_count = get_cpu_count(cfg)

    timebase_freq = {"timebase_freq": dt_get_timebase_frequency(cfg)}
    cpu_nodes.update(timebase_freq)

    for cpu in range(0, cpu_count):
        # interrupt controller
        intc = dt_create_interrupt_controller_node(is_zephyr=is_zephyr)
        intc_label = "L{0}".format(cpu)
        if is_zephyr:
            intc_label = "hlic{0}".format(cpu)
        intc['interrupt-controller']['label'] = intc_label

        core = "core{}".format(cpu)
        cpu_node = get_cpu_metadata(cfg, cpu, is_zephyr)
        cpu_node = dt_insert_child_node({core: cpu_node}, intc)
        cpu_nodes.update(cpu_node)

    parent = dt_create_parent_node(cfg, name, 1, 0)
    parent = dt_insert_child_node(parent, cpu_nodes)

    return parent

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
        reg = "reg = <{0} DT_SIZE_K({1})>;".format(addr, size)

    else:
        conf = load_config_file()
        # addr use linux start addr
        addr = conf['memory_mapped']['uImage']
        size = hex(int(size,0) - int(addr, 0))
        reg = "reg = <{0} {1}>;".format(addr, size)

    mem_node = {
        "label": label,
        "name": name,
        "device_type": 'device_type = "memory";',
        "addr": addr.lstrip('0x'),
        "size": size,
        "reg": reg
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


def dt_create_root_node(is_zephyr=False):
    root_node = {
            "root": {
                "name": "/",
                "version": dt_version(),
                "model": dt_model(),
                "addr_cell": 1,
                "size_cell": 1
                }
            }
    if is_zephyr:
        del root_node["root"]["version"]

    return root_node

"""
dt_get_bus_range: get the bus address range

@cfg (list): raw data of soc.h
@bus_name (str): can be PERIPHERAL_BMB, DDR_BMB, AXI_A_BMB

return: string of device tree ranges property
"""
def dt_get_bus_range(cfg, bus_name):
    addr = get_property_value(cfg, bus_name, bus_name + ' ')
    if not addr:
        print("Error: address for {} is invalid".format(bus_name))

    size = get_property_value(cfg, bus_name, "SIZE ")
    if not size:
        keyword_size = '{}_SIZE'.format(bus_name)
        print("Error: size for {0} is invalid. Expecting {1}".format(bus_name, keyword_size))

    ranges = "ranges = <0x0 {0} {1}>;".format(addr, size)
    return ranges


def dt_create_bus_node(cfg, bus_name, bus_label):
    bus_node = dt_create_parent_node(cfg, bus_label, 1, 1)
    bus_range = dt_get_bus_range(cfg, bus_name)
    addr = get_property_value(cfg, bus_name, bus_name + ' ').lstrip('0x')
    bus_node[bus_label].update({'ranges': bus_range})
    bus_node[bus_label].update({'addr': addr})

    return bus_node

def dt_create_soc_node(cfg):
    soc_node = dt_create_parent_node(cfg, "soc", 1, 1, is_zephyr=True)

    return soc_node

def __dt_parser_nodes_recursive(nodes, parent_node, count):
    out = ''
    out_temp = ''
    count += 1

    for k in nodes:
        if isinstance(nodes[k], dict):
            out_temp = __dt_create_node_str(nodes[k], parent_node)
            out_temp = indent(out_temp, count)
            out += out_temp
            out += __dt_parser_nodes_recursive(nodes[k], parent_node, count)
            out_temp = "};\n"
            out_temp = indent(out_temp, count)
            out += out_temp

    return out

"""
dt_parser_nodes: parser nodes to device tree format

@nodes (dict): nested dict node of paripheral
@parent_node (dict): parent node of @nodes or same level

return: String of nodes in device tree format
"""
def dt_parser_nodes(nodes, parent_node):
    out = ''
    out_temp = ''
    end_braces = True

    for k in nodes:
        n_node = nodes[k]
        out += __dt_create_node_str(n_node, parent_node)
        out1 = __dt_parser_nodes_recursive(n_node, parent_node, 0)

        if out1:
            out1 += "};\n"
            out += out1

        else:
            out += "};\n"

    return out

"""
create_dts_file: create dts file

@cfg (list): raw data of soc.h
@bus_node: node that contain all peripherals connected to it

return: string of nodes
"""
def create_dts_file(cfg, bus_node, is_zephyr=False, soc_name=None):
    dts_root_node = dt_create_root_node()
    node = {}
    nodes = {}

    conf = load_config_file()

    if is_zephyr:
        inc_file = {
            "#include": conf['zephyr_dts']['#include']
        }
        inc_file["#include"][0] += soc_name
        if (memory_selection == 'ext'): # external memory selected
            dts_root = conf['zephyr_dts']['root_ext']
        else:
            dts_root = conf['zephyr_dts']['root']
    else:
        inc_file = {
            "include": conf['dts']['include'],
            "#include": conf['dts']['#include']
        }
        dts_root = conf['dts']['root']

    dts_root_node['root'].update(inc_file)
    dts_root_node['root'].update(dts_root)

    mem_node = None
    if not is_zephyr:
        # memory
        mem_node=  dt_create_memory_node(cfg, False, False)


    if mem_node:
        dts_root_node = dt_insert_child_node(dts_root_node, mem_node)
    dts = dt_parser_nodes(dts_root_node, dts_root_node)

    for k in bus_node:
        n_node = bus_node[k]
        for periph in n_node:
            if isinstance(n_node[periph], dict):
                if 'status' in n_node[periph]:
                    if 'disabled' in n_node[periph]['status']:
                        node = {
                            "name": dt_get_phandle(n_node, periph),
                            "status": get_status(okay=True)
                        }

                        label = n_node[periph]['label']
                        if label in conf['dts']:
                            node.update(conf['dts'][label])

                        nodes.update({periph: node})

    dts += dt_parser_nodes(nodes, nodes)

    return dts

def create_includes(conf, is_zephyr=False):
    inc_file = {}

    if is_zephyr:
        inc_file = {
            "#include": [
                conf['zephyr_dtsi']['includes'][0],
                conf['zephyr_dtsi']['includes'][1]
            ]
        }
    return inc_file