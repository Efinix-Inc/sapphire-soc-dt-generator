from config_parser import ConfigParser
from device_node import DeviceNode
from soc_configs import SocConfigs
from util import *

class RootNode(DeviceNode):
    def __init__(self, configs, user_configs=None, arch=32):
        super().__init__(configs, "root", instance="", user_configs=user_configs, arch=arch)
        self.parser = ConfigParser(configs)
        self.dev_type = "soc"
        self.soc = SocConfigs(configs, self.dev_type, arch)

    def create_root_node(self, **metadata):
        """Create root node metadata"""
        root = {
            "version": "/dts-v1/",
            "header": "/",
            "frequency": self.soc.get_frequency(),
            "cpu_name": self.get_cpu_name()
        }

        if metadata:
            root.update(metadata)

        self.create_node()
        self.node.update(root)

        return self.node

    def get_cpu_name(self):
        """Return cpu name by lookup from self.user_configs"""
        if "cpu_name" in self.user_configs:
            if isinstance(self.user_configs["cpu_name"], dict):
                if str(self.arch) in self.user_configs["cpu_name"]:
                    cpu_type = self.soc.get_cpu_type()
                    return self.user_configs["cpu_name"][str(self.arch)][cpu_type]
            elif isinstance(self.user_configs["cpu_name"], str):
                return self.user_configs["cpu_name"]
        return None

    def create_cpu_node(self, label="cpus", instance=0):
        """Create cpu node"""
        dev_type = "cpu"
        addr_cells = 1
        cpu = DeviceNode(self.configs, dev_type, instance=instance,
                         user_configs=self.user_configs, arch=self.arch)
        cpu_node = cpu.create_node(dev_type=dev_type, label=label, instance=instance,
                                   parent_label="/", status=1, addr_cells=addr_cells,
                                   size_cells=0)
        header = cpu.generate_node_header(addr=instance, dev_type=dev_type)
        child_node = cpu_node.get("child", {})

        irq_label = f"intc{instance}"
        irq_ctrl = {
            "label": irq_label,
            "header": cpu.generate_node_header(dev_type="interrupt-controller",
                                               label=irq_label, reg=False)
        }
        caches = self.soc.get_cpu_caches()
        # create a copy of child node, else it keep reference to the same child node
        child_node = child_node.copy()
        child_node.update(irq_ctrl)

        properties = {
            "device_type": dev_type,
            "isa": self.soc.get_cpu_isa(),
            "mmu_type": self.soc.get_cpu_mmu_type(),
            "header": header,
            "reg": cpu.set_node_reg(instance, 0, addr_cells=addr_cells),
            "machine_type": self.arch,
            **caches,
            "child": child_node
        }

        cpu_node.update(properties)
        self._update_interrupt_extended(irq_label)

        return cpu_node

    def _update_interrupt_extended(self, irq_label):
        """update interrupt-extended properties"""

        prefix = f"&{irq_label} "
        insert_custom_target_string(self.user_configs, target_key="interrupts_extended",
                                         inserted_key="irq_extended", prefix="", index=prefix)

    def _create_memory_node(self, label, dev_type):
        """Create memory node"""
        mem = DeviceNode(self.configs, dev_type, user_configs=self.user_configs, arch=self.arch)
        self.mem_node = mem.create_node(label=label, parent_label="/", status=1)
        self.mem_node["device_type"] = label

        return self.mem_node

    def create_memory_node(self):
        return self._create_memory_node("memory", "ddr")

    def create_internal_memory_node(self):
        return self._create_memory_node("memory", "ram")

    def create_custom_nodes(self):
        """Create custom nodes which place in the root"""
        custom_nodes = {}
        dev_type = "custom"
        cstm_nodes = self.user_configs.get("custom", {})
        num = 0
        for k in cstm_nodes.keys():
            cstm = DeviceNode(self.configs, dev_type, instance=num, user_configs=self.user_configs, arch=self.arch)
            custom_nodes[k] = cstm.create_node(parent_label="root", label=k, status=1)
            num += 1

        return custom_nodes
