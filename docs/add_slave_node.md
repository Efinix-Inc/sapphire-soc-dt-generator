# Add Slave Node

The slave node could be added using `-s` or `--slave` argument of `device_tree_generator.py`. The slave node for a peripheral will be added into dts file. It should follow specific data structure to add the node.

For example, to add i2c based pressure sensor slave device to `i2c0` device tree node in dts file, create a file called `slave.json` with the following content.

```json
{
    "child": {
        "i2c_pressure_sensor": {
            "parent_label": "i2c0",
            "name": "pressure",
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

`name` - (required). The name of the node

`addr` - (required). Starting address of the device node

`label` - (optional). Set the lable for a node.

`compatible` - (optional). Driver name for the device

`private_data` - (optional). Device specific data which does not fit with any property.

## Example Usage

```python
./device_tree_generator.py -s slave.json /path/to/soc.h ti180 linux
```
