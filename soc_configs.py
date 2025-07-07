from controller import Controller

class SocConfigs(Controller):
    def __init__(self, configs):
        super().__init__(configs, dev_type="soc")
        self.configs = configs

    def get_frequency(self):
        """Return the peripherals frequency"""
        return self.configs.get("frequency", 0)

    def get_cpu_isa(self):
        """Return the cpu RISCV ISA"""
        return self.configs.get("cpus", {}).get("isa", "")

    def get_cpu_count(self):
        """Return number of cpu cores"""
        return self.configs.get("cpus", {}).get("cores", 0)

    def get_peripherals_configs(self):
        """Return the peripherals configurations"""
        return self.configs.get("peripherals", {})
