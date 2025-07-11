from config_parser import ConfigParser
from device_node import DeviceNode
from soc_configs import SocConfigs

class RootNode(DeviceNode):
    def __init__(self, configs, arch=32):
        super().__init__(configs, "root", arch=arch)
        self.configs = configs
        self.arch = arch
        self.node = {}
        self.addr_cells = self._set_cells(-1)
        self.size_cells = self._set_cells(-1)
        self.parser = ConfigParser(configs)
        self.dev_type = "soc"
        self.soc = SocConfigs(configs, self.dev_type, arch)

    def create_root_node(self, **metadata):
        """Create root node metadata"""
        root = {
            "version": "/dts-v1/",
            "header": "/",
            "frequency": self.soc.get_frequency()
        }

        if metadata:
            root.update(metadata)

        self.create_node()
        self.node.update(root)

        return self.node

    def create_cpu_node(self, label="cpus", instance=0, user_configs=None):
        """Create cpu node"""
        dev_type = "cpu"
        cpu = DeviceNode(self.configs, dev_type=dev_type, arch=self.arch)
        self.cpu_node = cpu.create_node(dev_type=dev_type, label=label, instance=instance,
                                         size_cells=0, parent_label="/", status=1)
        header = cpu.generate_node_header(instance, dev_type=dev_type)
        reg = cpu.set_node_reg(instance, 0)

        metadata = {
            "device_type": dev_type,
            "isa": self.soc.get_cpu_isa(),
            "mmu_type": self.soc.get_cpu_mmu_type(),
            "header": header,
            "reg": reg,
            "compatible": "riscv",
            "machine_type": self.arch
        }
        self.cpu_node.update(metadata)

        if user_configs:
            cpu.apply_user_configs(user_configs)

        return self.cpu_node

    def create_memory_node(self, label="memory", user_configs=None):
        """Create memory node"""
        dev_type = "ddr"
        peripherals_config = self.configs.get("peripherals", {})
        mem = DeviceNode(peripherals_config, dev_type=dev_type, arch=self.arch)
        self.mem_node = mem.create_node(label=label, parent_label="/", status=1)
        self.mem_node["device_type"] = "memory"
        if user_configs:
            print("create_memory_node: apply user configs")
            mem.apply_user_configs(user_configs)

        return self.mem_node
