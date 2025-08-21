# Add Child Node

The child node could be added using `-c` or `--user-configs` argument of `device_tree_generator.py`. The child node for a peripheral will be added into dts file. It should follow specific data structure to add the node.

For example, to add i2c based pressure sensor slave device to `i2c0` device tree node in dts file, create a file called `i2c.json` with the following content.

```json
{
    "child": {
        "i2c_pressure_sensor": {
            "address_cells": 1,
            "size_cells": 0,
            "parent_label": "i2c0",
            "label": "pressure@77",
            "addr": "0x77",
            "compatible": "bosch,bmp085",
            "private_data": [
                "vddd-supply = <&foo>;",
                "vdda-supply = <&bar>;"
            ]
        }
    }
}
```

`child` - (required). The keyword is require to tell `device_tree_generator.py` to create a node which is child of `parent_label`.

`i2c_pressure_sensor` - (required). The name of the node to be added. Could be any name.

`parent_label` - (required). Specify the parent of this node. See the [naming convention](device_tree_nodes.md) for parent_label.

`addr` - (required). Starting address of the device node

`label` - (required). Set the lable for a node.

`address_cells` - (optional). Set to 1 if child node has address-mapping or `reg` property.

`size_cells` - (optinal). Set to 0 if child node do not have a size component in `reg` property.

`compatible` - (optional). Driver name for the device

`private_data` - (optional). Device specific data which does not fit with any property.

## Example Usage

```python
./device_tree_generator.py -c i2c.json /path/to/soc.h ti180 linux
```

The output of generated device node for this i2c device is located in dts file as follows.

```
&i2c0 {
        #address-cells = <1>;
        #size-cells = <0>;
        status = "okay";

        pressure@77 {
                status = "okay";
                reg = <0x77>;
                compatible = "bosch,bmp085";
                vddd-supply = <&foo>;
                vdda-supply = <&bar>;
        };
};
```
