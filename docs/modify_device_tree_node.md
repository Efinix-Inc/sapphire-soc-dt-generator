# Modify Device Tree Nodes

Device tree nodes for peripherals could be overrided using json configuration file. The file should follow the specific format and passed `-c` or `--user-config` argument to `device_tree_generator.py`. The node name should follow the [node naming convention](device_tree_nodes.md).

For example, the snipped below in `overrides.json` to override the `compatible` property for `I2C_0` node.

The `overrides` key is needed to let the `device_tree_generator.py` know that it want to override the property of `I2C_0` node.

```json
{
    "overrides": {
        "I2C_0": {
            "compatible": "i2c-gpio"
        }
    }
}
```

## Example Usage

```
./device_tree_generator.py -c overrides.json /path/to/soc.h ti180 linux
```


