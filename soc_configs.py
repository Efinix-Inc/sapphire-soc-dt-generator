from controller import Controller

class SocConfigs(Controller):
    def __init__(self, configs):
        super().__init__(configs, dev_type="soc")
        self.configs = configs

    def get_frequency(self):
        return self.configs.get("frequency", 0)

    def get_cpu_isa(self):
        return self.configs.get("cpus", {}).get("isa", "")
