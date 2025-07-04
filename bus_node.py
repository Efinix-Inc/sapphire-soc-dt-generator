from controller import Controller
from device_node import DeviceNode

class BusNode(DeviceNode):
    def __init__(self, configs, bus_name, list_ctrl, arch=32):
        super().__init__(configs, dev_type=bus_name)
        self.configs = configs
        self.bus_name = bus_name
        self.ctrl = Controller(configs)
        self.list_ctrl = list_ctrl
        self.arch = arch
        self.bus_node = {}

    def get_ctrl_instances_by_address_range(self, bus_instance=0):
        """Return key-value mapping of controller and instances based on list_ctrl within address range"""
        dev = {}

        addr = self.ctrl.get_controller_address(self.bus_name, bus_instance)
        size = self.ctrl.get_controller_address_size(self.bus_name, bus_instance)

        if addr == -1 or size == -1:
            print(f"Error: address or size of the bus '{self.bus_name}' was not found")
            return dev

        end_addr = int(addr, 16) + int(size, 16)
        for ctrl in self.list_ctrl:
            instances = self.ctrl.filter_instances_by_address_range(addr, end_addr, ctrl)
            if instances:
                dev.update({ctrl: instances})
        return dev

    def create_bus_node(self, bus_instance=0):
        """Create a bus node"""
        metadata = {
            "ranges": self.get_bus_ranges(bus_instance=bus_instance),
            "peripherals": {}
        }
        self.bus_node = self.create_node(instance=bus_instance)
        self.update_node(self.bus_node, **metadata)

        return self.bus_node

    def populate_controller_instances_nodes(self, bus_instance=0, offset=True):
        """Populate bus node with controller instances"""
        ctrl_nodes = {}

        ctrls = self.get_ctrl_instances_by_address_range(bus_instance)
        if ctrls:
            for ctrl_type, ctrl_instances in ctrls.items():
                for ctrl_instance in ctrl_instances:
                    # Instantiate a new DeviceNode for each ctrl_instance
                    num = self.ctrl.get_instance_number(ctrl_type, ctrl_instance)
                    dn = DeviceNode(self.configs, ctrl_type, instance=num, arch=self.arch)
                    ctrl_node = dn.create_node(instance=num)

                    if offset:
                        header, reg = self.use_addr_offset(ctrl_node, bus_instance)
                        ctrl_node.update({"header": header, "reg": reg})

                    ctrl_nodes.update({ctrl_instance: ctrl_node})


        self.bus_node["peripherals"] = ctrl_nodes

        return self.bus_node

    def get_bus_ranges(self, bus_name=None, bus_instance=0):
        """Get the address-mapping range for a bus"""

        if bus_name is None:
            bus_name = self.bus_name

        addr = self.ctrl.get_controller_address(bus_name, bus_instance)
        size = self.ctrl.get_controller_address_size(bus_name, bus_instance)

        if self.arch == 64:
            addr_range = f"0x0 0x0 {addr} 0x0 {size}"
        else:
            addr_range = f"0x0 {addr} {size}"

        return f"<{addr_range}>;"

    def get_dev_instance_addr_offset(self, dev_node, bus_instance=0):
        """Calculate controller address offset from bus address"""
        bus_addr = self.ctrl.get_controller_address(self.bus_name, bus_instance)
        ctrl_addr = dev_node.get("addr", 0)

        return int(ctrl_addr, 16) - int(bus_addr, 16)

    def use_addr_offset(self, dev_node, bus_instance=0):
        """Generate a node header and reg based on address offset"""
        label = dev_node.get("label", "")
        dev_type = dev_node.get("type", "")
        size = dev_node.get("size", 0)

        offset_addr = self.get_dev_instance_addr_offset(dev_node, bus_instance)
        header = self.generate_node_header(label, dev_type, offset_addr)
        reg = self.set_node_reg(offset_addr, size)

        return header, reg
