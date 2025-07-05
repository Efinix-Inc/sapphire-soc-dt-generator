from config_parser import ConfigParser
from device_node import DeviceNode

class RootNode(DeviceNode):
    def __init__(self, configs, arch=32):
        super().__init__(configs, "root", arch=arch)
        self.configs = configs
        self.arch = arch
        self.node = {}
        self.addr_cells = self._set_cells(-1)
        self.size_cells = self._set_cells(-1)
        self.parser = ConfigParser(configs)

    def create_root_node(self, metadata=None):
        """Create root node metadata"""
        root = {
            "version": "/dts-v1/",
            "header": "/",
            "frequency": self.parser.get_frequency(self.configs)
        }

        if metadata:
            root.update(metadata)

        self.create_node()
        self.node.update(root)

        return self.node

