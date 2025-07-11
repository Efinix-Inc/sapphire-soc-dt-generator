class Controller:
    def __init__(self, configs, dev_type=None):
        self.configs = configs
        self.dev_type = dev_type
        self.ctrl_configs = configs.get("peripherals", {})

    def _check_dev_type(self, dev_type):
        dev_type = dev_type or self.dev_type
        if not dev_type:
            raise ValueError("Device type must be specified.")

    def _get_instance_data(self, dev_type=None, instance=0):
        """Retrive the configuraton data for a specific device type and instance"""
        self._check_dev_type(dev_type)
        return self.ctrl_configs.get(dev_type, {}).get(f"{dev_type}{instance}", {})

    def get_controller(self, dev_type=None, instance=0):
        """Return the full controller configuration for the given device type and instance"""
        return self._get_instance_data(dev_type, instance)

    def get_controller_address(self, dev_type=None, instance=0):
        """Return the address of the controller or -1 if not found"""
        return self._get_instance_data(dev_type, instance).get("addr", -1)

    def get_controller_address_size(self, dev_type=None, instance=0):
        """Return the address size of the controller or -1 if not found"""
        return self._get_instance_data(dev_type, instance).get("size", -1)

    def get_controller_interrupts_line(self, dev_type=None, instance=0):
        """Return the interrupts line of the controller or 0 if not found"""
        return self._get_instance_data(dev_type, instance).get("interrupts", 0)

    def get_controller_driver_name(self, dev_type=None, instance=0):
        """Return the controller driver name or empty string if not found"""
        return self._get_instance_data(dev_type, instance).get("compatible", "")

    def list_instances(self, dev_type=None):
        """Return a list of available instance names for the given device type"""
        self._check_dev_type(dev_type)
        return list(self.ctrl_configs.get(dev_type, {}).keys())

    def list_all_instances(self):
        """Return a flat list of all instance names across all device types"""
        return [name for instances in self.ctrl_configs.values() for name in instances]

    def list_all_controllers(self):
        """Return a list of all controller types (device types)"""
        return list(self.ctrl_configs.keys())

    def filter_instances_by_address_range(self, start, end, dev_type=None):
        """Return instances whose address falls within the given range"""
        filtered = []
        dev_types = [dev_type] if dev_type else self.ctrl_configs.keys()

        for dtype in dev_types:
            for name, data in self.ctrl_configs.get(dtype, {}).items():
                addr = data.get("addr")
                if addr is not None and int(start, 16) <= int(addr, 16) < int(end):
                    filtered.append(name)
        return filtered

    def update_controller(self, dev_type, instance, **kwargs):
        """Append multiple key-value pairs to a specific controller instance"""
        instance_name = f"{dev_type}{instance}"
        instance_data = self.ctrl_configs.setdefault(dev_type, {}).setdefault(instance_name, {})
        instance_data.update(kwargs)

    def get_instance_name(self, instance=0):
        if not self.dev_type is None:
            return f"{self.dev_type}{instance}"
        else:
            return None

    def get_instance_number(self, dev_type, dev_name):
        return ''.join([char for char in dev_name if char not in dev_type])
