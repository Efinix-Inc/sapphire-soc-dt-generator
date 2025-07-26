from controller import Controller

class SocConfigs(Controller):
    def __init__(self, configs, dev_type=None, arch=32):
        super().__init__(configs, dev_type)
        self.arch = arch

    def get_frequency(self):
        """Return the peripherals frequency"""
        return self.configs.get("frequency", 0)

    def _get_cpus_configs(self):
        return self.configs.get("cpus", {})

    def get_cpu_caches(self):
        """Return the cpu caches metadata"""
        cpu_configs = self._get_cpus_configs()
        return cpu_configs.get("caches", {})

    def get_cpu_type(self):
        """Return 1 for hardcore or 0 for softcore soc"""
        cpu_type = self._get_cpus_configs().get("cpu_type", 0)
        return "hard" if cpu_type == "1" else "soft"

    def get_cpu_isa(self):
        """Return the cpu RISCV ISA"""
        cpu_configs = self._get_cpus_configs()
        isa = cpu_configs.get("isa", "")
        if self.arch == "64":
            return f"rv64{isa}"
        elif self.arch == "32":
            return f"rv32{isa}"
        else:
            return ""

    def get_cpu_count(self):
        """Return number of cpu cores"""
        cpu_configs = self._get_cpus_configs()
        return cpu_configs.get("cores", 0)

    def get_cpu_mmu_type(self):
        """Return the RISCV mmu type"""
        if self.arch == "64":
            return "riscv,sv39"
        elif self.arch == "32":
            return "riscv,sv32"
        else:
            return ""

    def get_peripherals_configs(self):
        """Return the peripherals configurations"""
        return self.configs.get("peripherals", {})
