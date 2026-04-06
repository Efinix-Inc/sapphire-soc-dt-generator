import sys
import re
import json
from collections import defaultdict

class ConfigParser:
    def __init__(self, configs):
        self.configs = configs
        self.pattern = re.compile(r"#define\s+(\w+)\s+(\w+)")
        self.macros = {}
        self.parsed_configs = defaultdict()
        self.peripherals = defaultdict(lambda: defaultdict(lambda: {"interrupts": []}))
        self.warnings = []
        self.trace = defaultdict(list)

    def _parse_macros_to_dict(self):
        """Collect all macro key-value definitions"""
        for macro, value in self.pattern.findall(self.configs):
            self.macros[macro] = value

    def _parse_address_size_macros(self):
        """Handles address/size macros (e.g., *_INPUT, *_CTRL, *_IO_CTRL, *_SIZE)"""
        suffix_map = {
            "addr": ("IO_CTRL", "CTRL", "INPUT", "BMB", "BASE"),
            "size": ("CTRL_SIZE", "INPUT_SIZE", "BMB_SIZE", "BASE_SIZE")
        }

        for macro, raw_value in self.macros.items():
            resolved_value = self._resolved_value(raw_value)
            dev_type, dev_num = self._get_dev_type_and_num(macro)
            dev_key = f"{dev_type}{dev_num}"

            for key, suffixes in suffix_map.items():
                if any(macro.endswith(suffix) for suffix in suffixes):
                    self.peripherals[dev_type][dev_key][key] = resolved_value
                    self.trace[f"{dev_type}.{dev_key}"].append((macro, key))
                    break

    def _parse_interrupt_macros(self):
        """Handle nested interrupt macro (e.g., SYSTEM_PLIC_SYSTEM_UART_0_IO_INTERRUPT_X)"""
        for macro, target in self.macros.items():
            if "INTERRUPT" in macro:
                prefix = "SYSTEM_PLIC_"
                if macro.startswith(prefix):
                    macro = macro[len(prefix):]

                value = self._resolved_value(target)
                dev_type, dev_num = self._get_dev_type_and_num(macro)
                dev_key = f"{dev_type}{dev_num}"

                self.peripherals[dev_type][dev_key]["interrupts"].append(value)
                self.trace[f"{dev_type}.{dev_key}"].append((macro, "interrupts"))

    def _get_dev_type_and_num(self, macro):
        """Get the dev type (e.g., spi, uart, i2c) and the instance number (e.g., 0, 1)"""
        parts = macro.split('_')
        
        try:
            dev_type = parts[1].lower()
            dev_num = parts[2]

            if "apb" in dev_type:
                dev_num = parts[3]
                dev_type = f"{dev_type}_{parts[2].lower()}"

            if "axi" in dev_type:
                if "slave" in parts[2].lower():
                    dev_num = parts[3]
                    dev_type = f"{dev_type}_{parts[2].lower()}"
                else:
                    dev_num = str(self.to_num(parts[2]))

            if not dev_num.isdigit():
                dev_num = 0

            return dev_type, dev_num

        except IndexError:
            return None, None

    def parse(self):
        """Parse the self.configs by creating a data structure which consists of device type, address, size and interrupt number"""
        self._parse_macros_to_dict()
        self._parse_address_size_macros()
        self._parse_interrupt_macros()
        self.parse_cpu_macros()

        self.parse_frequency()
        self.parsed_configs["peripherals"] = self.peripherals
        return self.parsed_configs

    def _resolved_value(self, val, trail=None):
        """Convert hex/int literals or resolve nested macro references"""
        trail = trail or []

        if val.endswith("U"):
            val = val.replace("U", "")
        if val.startswith("0x") or val.isdigit():
            return val
        elif val in self.macros:
            if val in trail:
                self.warnings.append(f"Circular reference detected: {' -> '.join(trail + [val])}")
                return val
            return self._resolved_value(self.macros[val], trail + [val])
        else:
            self.warnings.append(f"Unresolvable value: {val}")
            return val # fallback: leave as string

    def report(self):
        if self.warnings:
            print("Warnings: ")
            for w in self.warnings:
                print(f" - {w}")
        if self.trace:
            print("\nTrace information:")
            for key, entries in self.trace.items():
                print(f" [{key}]")
                for macro, field in entries:
                    print(f"  - {field} set from macro: {macro}")

    def get_parse_config(self):
        return self.peripherals

    def to_json(self, indent=2):
        return json.dumps(self.parsed_configs, indent=indent)

    def parse_cpu_macros(self):
        """Parse cpu number, ISA, and other metadata"""
        cpu_count = self.get_cpu_count()
        if cpu_count < 1:
            print("Error: CPU information not found!")
            sys.exit(1)

        cpu = {
            "cores": cpu_count,
            "isa": self._get_cpu_isa(),
            "caches": self._parse_cpu_caches(),
            "cpu_type": self._parse_cpu_type()
        }

        self.parsed_configs["cpus"] = cpu

    def get_cpu_count(self):
        cpus = self.search_macro_pattern('SYSTEM_NUMBER_OF_HARTS')
        if int(cpus) > 0:
            return int(cpus)

        cpus = self.peripherals.get("cores", {})
        return len(cpus.keys()) if cpus else 0

    def _get_cpu_isa(self):
        """Get cpu instruction set strings"""
        # Canonical ordering
        single_letter_order = ["m", "a", "c", "f", "d"]
        z_ext_order = [
            "zicsr",
            "zifence",
            "zifencei",
            "zba",
            "zbb",
            "zbs",
            "zicbom",
        ]

        # Detect base ISAs
        has_rv32 = self.search_macro_pattern("SYSTEM_RISCV_ISA_RV32I")
        has_rv64 = self.search_macro_pattern("SYSTEM_RISCV_ISA_RV64I")

        # Collect enabled extensions
        enabled = set()
        for macro, value in self.macros.items():
            if value != "1":
                continue

            m = re.search(r"ISA_(EXT_)?(.+)", macro)
            if not m:
                continue

            ext = m.group(2).lower()
            enabled.add(ext)

        if has_rv32:
            isa = "rv32i"

        if has_rv64:
            isa = "rv64i"

        # Single-letter extensions
        for ext in single_letter_order:
            if ext in enabled:
                isa += ext

        # Z-extensions
        for z in z_ext_order:
            if z in enabled:
                if "zifence" in z:
                    isa += "_zifencei"
                else:
                    isa += f"_{z}"

        return isa

    def parse_frequency(self):
        """get frequency defined by clint_hz"""
        pattern = re.compile(r"HZ")
        for macro, value in self.macros.items():
            for macro in pattern.findall(macro):
                self.parsed_configs["frequency"] = value

    def to_num(self, char):
        """Convert a character to its corresponding number. 'a' or 'A' -> 1, 'b' or 'B' -> 2 and so on"""
        if char.isalpha() and len(char) == 1:
            return ord(char.lower()) - ord('a')
        else:
            return 0

    def _parse_cpu_caches(self):
        """Parse all cpu caches information"""
        patterns = (
            "ICACHE_WAYS",
            "ICACHE_SIZE",
            "DCACHE_WAYS",
            "DCACHE_SIZE",
            "BYTES_PER_LINE",
            "L2_CACHE_SIZE",
            "L2_CACHE_WAYS",
        )

        cores = {}
        # Initialize caches to 0
        for pattern in patterns:
            cores[pattern.lower()] = 0

        # Populate the caches
        for key, value in self.macros.items():
            for field in patterns:
                if key.endswith(field):
                    cores[field.lower()] = value

        return cores

    def _parse_cpu_type(self):
        """Parse cpu type like softcore or hardcore. Return 1 for hardcore, 0 for softcore"""
        return self.search_macro_pattern("SYSTEM_HARD_RISCV_QC32")

    def search_macro_pattern(self, pattern):
        """Parse macro pattern and return the value if found, else return 0"""
        search = re.compile(rf"{pattern}")

        for k, v in self.macros.items():
            for k in search.findall(k):
                return v

        return 0
