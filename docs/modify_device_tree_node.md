# Modify Device Tree Nodes

Device tree nodes for peripherals could be overrided using json configuration file. The file should follow the specific format and passed `-c` or `--user-config` argument to `device_tree_generator.py`. 

## Example Usage

This is an example to override the `axi_slave` device node with `mmc` device node.

The `overrides` key is needed to let the `device_tree_generator.py` know that it want to override the configuration. The `device_instance` is the device node name that would be get override. This configuration save as file named `mmc.json`.

```json
{
    "overrides": {
        "mmc": {
            "interface": "mmc",
            "label": "mmc0",
            "compatible": ["efx,sdhci"],
            "device_instance": "axi_slave1",
            "interrupts": ["19"],
            "private_data": [
                "bus-width = <4>;",
                "no-sdio;",
                "no-mmc;",
                "max-frequency = <100000000>;"
            ]
        }
    }
}
```

### Generate Device Tree with override configuration

```
./device_tree_generator.py -c mmc.json /path/to/soc.h ti180 linux
```

The output files such as `*.dtsi` and `*.dts`  stored in `output/{os_name}`, where `os_name` could be `linux`, `u-boot`, or `zephyr`. In this case, the parameter `linux` is specify when executing `device_tree_generator.py`. Thus, the output files should be in `output/linux`.

### Output .dtsi

```
axi1 {
    #address-cells = <1>;
    #size-cells = <1>;
    compatible = "simple-bus";
    ranges = <0x0 0xe9000000 0x10000>;

    mmc0: mmc@e9000000 {
        reg = <0x0 0x10000>;
        compatible = "efx,sdhci";
        interrupts = <19>;
        interrupt-parent = <&plic>;
        clocks = <&clock>;
        clock-frequency = <200000000>;
        status = "disabled";
    };
};
```

### Output .dts

```
&mmc0 {
    bus-width = <4>;
    no-sdio;
    no-mmc;
    max-frequency = <100000000>;
    status = "okay";
};
```
