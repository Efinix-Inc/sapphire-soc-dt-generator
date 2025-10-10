from soc_configs import SocConfigs
from util import *

class DeviceNode:
    def __init__(self, configs, dev_type, instance=0, user_configs=None, arch=32):
        self.configs = configs
        self.dev_type = dev_type
        self.instance = instance
        self.user_configs = user_configs
        self.arch = arch # machine architecture i.e., 32 or 64
        self.status = -1
        self.node = {}
        self.ctrl = SocConfigs(configs, dev_type, arch=arch)
        self.addr_cells = self._set_cells(-1)
        self.size_cells = self._set_cells(-1)

    def create_node(self, dev_type=None, instance=None, addr_cells=-1, size_cells=-1,
                    parent_label=None, status=0, label=None):
        """Create a device tree node of a device"""
        self.status = status
        self.addr_cells = self._set_cells(addr_cells)
        self.size_cells = self._set_cells(size_cells)
        self.instance = instance or self.instance

        dev_type = dev_type or self.dev_type
        label = label or self.ctrl.get_instance_name(self.instance)

        address_cells = self.set_address_cells(self.addr_cells)
        size_cells = self.set_size_cells(self.size_cells)
        # get the address mapping and size of the device
        addr = self.ctrl.get_controller_address(dev_type, self.instance)
        size = self.ctrl.get_controller_address_size(dev_type, self.instance)

        compatible = self.ctrl.get_controller_driver_name(dev_type, self.instance)
        interrupts = self.ctrl.get_controller_interrupts_line(dev_type, self.instance)

        self.node = {
                "device_instance": self.ctrl.get_instance_name(self.instance),
                "interface": dev_type,
                "device_type": None,
                "label": label,
                "parent_label": parent_label,
                # device tree specific properties
                "address_cells": address_cells,
                "size_cells": size_cells,
                "addr": addr,
                "size": size,
                "reg": self.set_node_reg(addr, size, address_cells, size_cells),
                "header": self.generate_node_header(addr, label, dev_type),
                "compatible": self.ctrl.get_controller_driver_name(dev_type, self.instance),
                "interrupts": self.ctrl.get_controller_interrupts_line(dev_type, self.instance),
                "interrupt_parent": None,
                "clocks": None,
                "clock_frequency": self.ctrl.get_frequency(),
                "private_data": [],
                "status": self._lookup_status(),
                "child": {}
        }

        if self.user_configs:
            self.apply_user_configs(self.instance)

        self.apply_os_overrides()

        return self.node

    def generate_node_header(self, addr=None, label=None, dev_type=None, reg=True):
        addr = addr if addr else self.node.get("addr", 0)
        if addr:
            addr = convert_to_hex(abs(convert_to_int(addr)))
            # handle prefix 0x in addr
            addr = str(addr)[2:]

        label = label if label else self.node.get("label", None)
        dev_type = dev_type if dev_type else self.node.get("interface", None)

        return self._generate_node_header(label, dev_type, addr, reg)

    def _generate_node_header(self, label, dev_type, addr, reg=True):
        header = ""
        if label:
            header = f"{label}"
            if dev_type:
                header += f": {dev_type}"
                if reg:
                    header += f"@{addr}"

        elif dev_type:
            header = f"{dev_type}"
            if reg:
                header += f"@{addr}"

        return header

    def set_node_reg(self, address, size, addr_cells=-1, size_cells=-1):
        def format_cells(value, cells):
            value = convert_to_hex(abs(convert_to_int(value)))
            if cells == 2:
                return f"0x0 {value}"
            elif cells == 1:
                return f"{value}"
            else:
                return "0x0"

        if addr_cells == -1:
            addr_cells = self.addr_cells
        if size_cells == -1:
            size_cells = self.size_cells

        reg_addr = format_cells(address, addr_cells)
        reg_size = format_cells(size, size_cells)

        if size_cells == 0:
            return f"{reg_addr}"
        else:
            return f"{reg_addr} {reg_size}"

    def update_node(self, **kwargs):
        """Append multiple key-value pairs to the specific device node"""
        self.node.update(kwargs)
        return self.node

    def get_device_node(self):
        """Return the device node data structure"""
        return self.node

    def _set_cells(self, value):
        self.arch = int(self.arch)
        if value != -1:
            return value
        elif self.arch == 32:
            return 1
        elif self.arch == 64:
            return 2
        else:
            return 0

    def set_address_cells(self, value=-1):
        return self._set_cells(value)

    def set_size_cells(self, value=-1):
        return self._set_cells(value)

    def get_address_cells(self):
        return self.node.get("address_cells", -1)

    def get_size_cells(self):
        return self.node.get("size_cells", -1)

    def _lookup_status(self, status=-1):
        """Set the status of device node"""
        if status == -1:
            status = self.status

        if status == 0:
            dev_status = "disabled"
        elif status == 1:
            dev_status = "okay"
        else:
            dev_status = "reserved"

        dev_status = f"{dev_status}"
        return dev_status

    def set_status(self, status):
        dev_status = self._lookup_status(status)
        self.node.update({"status": dev_status})

    def apply_user_configs(self, instance):
        """Modify the value of device node with user configs"""
        if self.user_configs is None:
            return

        drivers = self.user_configs.get("drivers", {})
        overrides = self.user_configs.get("overrides", {})
        children = self.user_configs.get("child", {})
        custom = self.user_configs.get("custom", {})

        for k, v in drivers.items():
            if self.dev_type == k:
                v = self._regenerate(v)
                self.update_node(**v)
                break

        for k, v in overrides.items():
            device_instance = overrides.get(k, {}).get("device_instance")
            if device_instance == self.ctrl.get_instance_name(instance):
                v = self._regenerate(v)
                self.update_node(**v)
                break

        self._process_children(children, self.node, instance)

        for k, v in custom.items():
            if self.dev_type == "custom":
                device_instance = v.get("device_instance")
                if device_instance == self.ctrl.get_instance_name(instance):
                    v = self._regenerate(v)
                    self.update_node(**v)
                    break

    def _process_children(self, children, node, instance):
        for k, v in children.items():
            parent_label = v.get("parent_label")
            device_instance = self.ctrl.get_instance_name(instance)

            if parent_label == device_instance:
                child_node = self._create_child_node(v)
                node["child"][k] = child_node

                # Recursively process the child if exists
                if "child" in v and isinstance(v["child"], dict):
                    for kc, vc in v["child"].items():
                        cchild_node = self._create_child_node(vc)
                        node["child"][k]["child"][kc] = cchild_node

    def _regenerate(self, new_values):
        """Regenerate 'reg' and 'header' property"""

        nheader = new_values.get("header")
        nreg = new_values.get("reg")
        naddr = new_values.get("addr")
        nsize = new_values.get("size")
        nlabel = new_values.get("label")
        dev_type = new_values.get("interface", self.dev_type)
        compatible = new_values.get("compatible")
        if compatible:
            if isinstance(compatible, list):
                new_values["compatible_str"] = self.get_compatible_string(compatible)
            else:
                new_values["compatible_str"] = f"\"{compatible}\""

        size = nsize if nsize else self.ctrl.get_controller_address_size(dev_type=dev_type)
        label = nlabel if nlabel else self.node.get("label", None)
        addr = naddr if naddr else self.node.get("addr", None)

        if nreg:
            # Set '_override_reg' to indicate that <user_config>.json override the reg value
            new_values["_override_reg"] = True

        if naddr:
            new_values.setdefault("header", self.generate_node_header(addr, label, dev_type))
            if not "_override_reg" in new_values:
                new_values.setdefault("reg", self.set_node_reg(addr, size))

        if nlabel:
            new_values.setdefault("header", self.generate_node_header(addr, label, dev_type))

        return new_values

    def get_compatible_string(self, compatibles_list):
        if isinstance(compatibles_list, list):
            return ', '.join(f'"{compatible}"' for compatible in compatibles_list)

    def _create_child_node(self, child_config):
        """Create a template of child node"""

        label = child_config.get("label")
        dev_type = child_config.get("interface")
        addr = child_config.get("addr", 0)
        size = child_config.get("size", 0)
        addr_cells = child_config.get("address_cells", self._set_cells(-1))
        size_cells = child_config.get("size_cells", self._set_cells(-1))
        reg = child_config.get("reg", self.set_node_reg(addr, size, addr_cells, size_cells))
        header = child_config.get("header", self._generate_node_header(label, dev_type, addr, reg=True))
        node = {
            "header": header,
            "label": label,
            "parent_label": child_config.get("parent_label"),
            "address_cells": addr_cells,
            "size_cells": size_cells,
            "addr": addr,
            "size": size,
            "reg": reg,
            "compatible": child_config.get("compatible"),
            "private_data": child_config.get("private_data", []),
            "status": child_config.get("status", "okay"),
            "child": child_config.get("child", {})
        }

        # append additionals key value pairs to the node
        for k, v in child_config.items():
            if k not in node:
                node[k] = v

        return node

    def apply_os_overrides(self):
        """Apply any operating system specific configuration"""

        interrupt_cells = self.node.get("interrupt_cells")
        priority = self.node.get("irq_priority", "1")
        interrupts = self.node.get("interrupts")

        if interrupt_cells and interrupts:
            interrupts = interrupts[:interrupt_cells]

        # zephyr require additional priority number in interrupts property with default is 1
        if "zephyr" in self.configs.get("os_name"):
            if interrupts:
                interrupts.append(str(priority))

        self.node["interrupts"] = interrupts
