from device_node import DeviceNode
from util import *

class BusNode(DeviceNode):
    def __init__(self, configs, bus_type, list_ctrl, bus_instance=0,
                 user_configs=None, arch=32):
        super().__init__(configs, bus_type, instance=bus_instance,
                         user_configs=user_configs, arch=arch)
        self.list_ctrl = list_ctrl

    def get_bus_devices(self, bus_instance=0):
        """Return key-value mapping of controller and instances based on list_ctrl within address range"""
        dev = {}

        addr = self.ctrl.get_controller_address(self.dev_type, bus_instance)
        size = self.ctrl.get_controller_address_size(self.dev_type, bus_instance)

        if addr == -1 or size == -1:
            print(f"Error: address or size of the bus '{self.dev_type}' was not found")
            return dev

        end_addr = int(addr, 16) + int(size, 16)
        for ctrl in self.list_ctrl:
            instances = self.ctrl.filter_instances_by_address_range(addr, end_addr, ctrl)
            if instances:
                dev.update({ctrl: instances})
        return dev

    def create_bus_node(self, bus_instance=0, header=None, label=None):
        """Create a bus node"""
        properties = {
            "ranges": self.get_bus_ranges(bus_instance=bus_instance),
            "peripherals": {}
        }
        if header:
            properties["header"] = f"{header}"

        self.node = self.create_node(instance=bus_instance, label=label)
        self.update_node(**properties)

        return self.node

    def populate_controller_instances_nodes(self, bus_instance=0, addr_offset=True):
        """Populate bus node with controller instances"""
        ctrl_nodes = {}

        ctrls = self.get_bus_devices(bus_instance)
        if ctrls:
            for ctrl_type, ctrl_instances in ctrls.items():
                ctrl_instances = self._filter_controller_instances(ctrl_instances)
                if ctrl_instances is None:
                    continue
                for ctrl_instance in ctrl_instances:
                    # Instantiate a new DeviceNode for each ctrl_instance
                    num = self.ctrl.get_instance_number(ctrl_type, ctrl_instance)
                    dn = DeviceNode(self.configs, ctrl_type, instance=num,
                                    user_configs=self.user_configs, arch=self.arch)
                    parent_label = self.ctrl.get_instance_name(num)
                    ctrl_node = dn.create_node(instance=num, parent_label=parent_label,
                                               addr_cells=1, size_cells=0, status=1)

                    header, reg = self._use_addr_offset(ctrl_node, bus_instance, use=addr_offset)
                    properties = {"header": header, "reg": reg}
                    dn.update_node(**properties)

                    # find phandle of interrupt-controller and clock
                    phandle_irq = self.get_interrupt_controller_phandle()
                    phandle_clk = self.get_clock_phandle()
                    properties = {
                        "interrupt_parent": phandle_irq,
                        "clocks": phandle_clk
                    }
                    dn.update_node(**properties)

                    ctrl_nodes.update({ctrl_instance: ctrl_node})

        self.node["peripherals"] = ctrl_nodes

        return self.node

    def get_bus_ranges(self, bus_type=None, bus_instance=0):
        """Get the address-mapping range for a bus"""

        bus_type = bus_type or self.dev_type

        addr = self.ctrl.get_controller_address(bus_type, bus_instance)
        size = self.ctrl.get_controller_address_size(bus_type, bus_instance)

        reg = self.set_node_reg(addr, size, addr_cells=self.addr_cells)
        if self.arch == 64:
            addr_range = f"0x0 0x0 {reg}"
        else:
            addr_range = f"0x0 {reg}"

        return f"{addr_range}"

    def get_dev_instance_addr_offset(self, dev_node, bus_instance=0):
        """Calculate controller address offset from bus address"""
        bus_addr = self.ctrl.get_controller_address(self.dev_type, bus_instance)
        ctrl_addr = dev_node.get("addr", 0)

        return int(ctrl_addr, 16) - int(bus_addr, 16)

    def _use_addr_offset(self, dev_node, bus_instance=0, use=True):
        """Generate a node header and reg based on address offset"""
        label = dev_node.get("label", "")
        dev_type = dev_node.get("interface", "")
        size = dev_node.get("size", 0)
        addr = dev_node.get("addr", 0)

        if use:
            addr = self.get_dev_instance_addr_offset(dev_node, bus_instance)

        header = self.generate_node_header(addr, label, dev_type)
        reg = self.set_node_reg(addr, size)

        return header, reg

    def list_bus_instances(self):
        return self.ctrl.list_instances(self.dev_type)

    def get_interrupt_controller_phandle(self):
        """Get phandle of interrupt controller node"""

        d = find_dict_with_key_value(self.user_configs, "_device_type_", "interrupt-controller")
        return self._get_phandle(d)

    def get_clock_phandle(self):
        """Get phandle of clock node"""
        d = find_dict_with_key_value(self.user_configs, "device_type", "clock")
        return self._get_phandle(d)

    def _get_phandle(self, d):
        if isinstance(d, dict):
            label = d.get("label", None)
            return f"&{label}" if label else None

        return None

    def _filter_controller_instances(self, instances):
        """Remove the controller instances based on blacklist."""
        blacklist = set(self.user_configs.get("blacklist_instances", []))
        return [item for item in instances if item not in blacklist]

