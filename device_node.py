from controller import Controller

class DeviceNode:
    def __init__(self, configs, dev_type, instance=0, arch=32):
        self.configs = configs
        self.dev_type = dev_type
        self.instance = instance
        self.arch = arch # machine architecture i.e., 32 or 64
        self.status = -1
        self.node = {}
        self.ctrl = Controller(configs, dev_type)
        self.addr_cells = self._set_cells(-1)
        self.size_cells = self._set_cells(-1)

    def create_node(self, dev_type=None, label=None, instance=0, addr_cells=-1, size_cells=-1, parent_label=None, status=0):
        """Create a device tree node of a device"""
        self.status = status
        self.addr_cells = self._set_cells(addr_cells)
        self.size_cells = self._set_cells(size_cells)

        if dev_type is None:
            dev_type = self.dev_type

        if label is None:
            label = self.ctrl.get_instance_name(self.instance)

        # get the address mapping and size of the device
        addr = self.ctrl.get_controller_address(dev_type, instance)
        size = self.ctrl.get_controller_address_size(dev_type, instance)

        self.node = {
                "address_cells": self.set_address_cells(self.addr_cells),
                "size_cells": self.set_size_cells(self.size_cells),
                "type": dev_type,
                "label": label,
                "parent_label": parent_label,
                "reg": self.set_node_reg(addr, size),
                "header": self.generate_node_header(addr, label, dev_type),
                "compatible": self.ctrl.get_controller_driver_name(dev_type),
                "private_data": [],
                "status": self._lookup_status()
        }
        if "interrupts" in self.configs:
            self.node.update({"interrupt-parent": "<&plic>"})

        dev = self.ctrl.get_controller(dev_type, instance)
        self.node.update(dev)

        return self.node

    def generate_node_header(self, addr, label=None, dev_type=None):
        addr = self.convert_to_hex(abs(self.convert_to_int(addr)))
        # handle prefix 0x in addr
        addr = str(addr)[2:]

        header = f"{dev_type}@{addr}"
        if not label is None:
            header = f"{label}: {header}"

        return header

    def set_node_reg(self, address, size):
        def format_cells(value, cells):
            value = self.convert_to_hex(abs(self.convert_to_int(value)))
            if cells == 2:
                return f"0x0 {value}"
            elif cells == 1:
                return f"{value}"
            else:
                return "0x0"

        reg_addr = format_cells(address, self.addr_cells)
        reg_size = format_cells(size, self.size_cells)

        if self.size_cells == 0:
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
        if value != -1:
            return value
        elif self.arch == "32":
            return 1
        elif self.arch == "64":
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

    def convert_to_int(self, s):
        if isinstance(s, str) and s.startswith("0x"):
            return int(s, 16)
        else:
            return int(s)

    def convert_to_hex(self, s):
        if isinstance(s, str):
            if s.startswith("0x"):
                value = int(s, 16)
            else:
                value = int(s)
        else:
            value = s # assume it's already an int

        return hex(value)

    def apply_user_configs(self, user_configs):
        """Modify the value of device node with user configs"""
        drivers = user_configs.get("drivers", {})
        overrides = user_configs.get("overrides", {})

        for k, v in drivers.items():
            if self.dev_type == k:
                self.update_node(**v)

        for k, v in overrides.items():
            if k == self.ctrl.get_instance_name(self.instance):
                v = self._regenerate(v)
                self.update_node(**v)

    def _regenerate(self, new_values):
        """Regenerate 'reg' and 'header' property"""

        # addr reg header regenerate
        #  0    0    0     no
        #  0    0    1     no
        #  0    1    0     no
        #  0    1    1     no
        #  1    0    0     yes (reg & header)
        #  1    1    0     yes (header)
        #  1    1    1     no

        nheader = new_values.get("header")
        nreg = new_values.get("reg")
        naddr = new_values.get("addr")
        nsize = new_values.get("size")
        nlabel = new_values.get("label")
        dev_type = new_values.get("type", self.dev_type)

        size = nsize if nsize else self.ctrl.get_controller_address_size(dev_type=dev_type)
        label = nlabel if nlabel else self.node.get("label", None)

        if naddr:
            new_values.setdefault("header", self.generate_node_header(naddr, label, dev_type))
            new_values.setdefault("reg", self.set_node_reg(naddr, size))

        return new_values
