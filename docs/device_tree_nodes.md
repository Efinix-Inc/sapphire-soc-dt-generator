# Device Tree Nodes

## Node Data Structure

The basic data structure for each node is as follows

```json
{
    "spi0": {
        "interface": "spi",
        "label": "spi0",
        "addr": 0x15000,
        "size": 0x1000,
        "compatible": "spinal-lib,spi-1.0",
        "private_data": [
            "cmd_fifo_depth = <256>;",
            "rsp_fifo_depth = <256>;",
            "num-cs = <1>;"
        ]
    }
}
```

`spi0` - Node name

`label` - label of the node (optional)

`addr` - start address of the device

`compatible` - driver name for the device

`private_data` - device specific data which not fit to any keyword of the node

This device node would be translated to device tree format as follows.

```
spi0: spi@15000 {
    "compatible" = "spinal-lib,spi-1.0";
    "reg" = <0x15000 0x1000>;
    "cmd_fifo_depth" = <256>;
    "rsp_fifo_depth" = <256>;
    "num-cs" = <1>;
    "status" = "okay";
};
```
