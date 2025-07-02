from controller import Controller

class DeviceNode:
    def __init__(self, dev_config, dev_type, instance=0, arch=32):
        self.dev_config = dev_config
        self.dev_type = dev_type
        self.instance = instance
        self.arch = arch # machine architecture i.e., 32 or 64
        self.status = -1
        self.node = {}
        self.ctrl = Controller(dev_config, dev_type)

    def create_node(self, dev_type=None, label=None, instance=0, addr_cells=1, size_cells=1, parent_label=None, status=0):
        """Create a device tree node of a device"""
        self.status = status

        if dev_type is None:
            dev_type = self.dev_type

        if label is None:
            label = self.ctrl.get_instance_name(self.instance)

        # get the address mapping and size of the device
        addr = self.ctrl.get_controller_address(dev_type, instance)
        size = self.ctrl.get_controller_address_size(dev_type, instance)

        self.node = {
                "#address-cells": self.set_address_cells(addr_cells),
                "#size-cells": self.set_size_cells(size_cells),
                "type": dev_type,
                "label": label,
                "parent_label": parent_label,
                "header": self.generate_node_header(label, dev_type, addr),
                "status": self._lookup_status()
        }
        if "interrupts" in self.dev_config:
            self.node.update({"interrupt-parent": "<&plic>"})

        self.set_node_reg(addr, size)

        dev = self.ctrl.get_controller(dev_type, instance)
        self.node.update(dev)

        return self.node

    def generate_node_header(self, label, dev_type, addr):
        # handle prefix 0x in addr
        addr = str(addr)[2:]

        header = f"{dev_type}@{addr} {{"
        if not label is None:
            header = f"{label}: {header}"

        return header

    def set_node_reg(self, address, size):
        def format_cells(value, cells):
            if cells == 2:
                return f"0x0 {value}"
            elif cells == 1:
                return f"{value}"
            else:
                return "0x0"

        addr_cells = self.get_address_cells()
        size_cells = self.get_size_cells()

        reg_addr = format_cells(address, addr_cells)
        reg_size = format_cells(size, size_cells)

        reg = {
            "reg": f"<{reg_addr} {reg_size}>;"
        }
        self.node.update(reg)

    def update_node(self, node_name, **kwargs):
        """Append multiple key-value pairs to the specific device node"""
        self.node.update(kwargs)
        return self.node

    def get_device_node(self):
        """Return the device node data structure"""
        return self.node

    def _set_cells(self, value):
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
        return self.node.get("#address-cells", -1)

    def get_size_cells(self):
        return self.node.get("#size-cells", -1)

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

        dev_status = f'"{dev_status}";'
        return dev_status

    def set_status(self, status):
        dev_status = self._lookup_status(status)
        self.node.update({"status": dev_status})
