# Device Tree Nodes

## Node Data Structure

The basic data structure for each node is as follows

```json
{
    "SPI_0": {
        "name": "spi",
        "label": "spi0",
        "addr": "15000",
        "compatible": "spinal-lib,spi-1.0",
        "private_data": [
            "cmd_fifo_depth = <256>;",
            "rsp_fifo_depth = <256>;",
            "num-cs = <1>;"
        ]
    }
}
```

`SPI_0` - Node name should follow node naming convention

`name` - name of the node

`label` - label of the node (optional)

`addr` - start address of the device

`compatible` - driver name for the device

`private_data` - device specific data which not fit to any keyword of the node

## Node Naming convention

The naming convention is the naming of device tree node used in the `device_tree_generator.py` script format. Here is a list of the available device tree node.

| Node Name   | Parent Label | Description            |
| ----------- | ------------ | ---------------------- |
| SPI_0       | spi0         | spi0 device node       |
| UART_0      | uart0        | uart0 device node      |
| I2C_0       | i2c0         | i2c0 device node       |
| GPIO_0      | gpio0        | gpio0 device node      |
| APB_SLAVE_0 | apb_slave_0  | apb_slave0 device node |

> Note: 
> 
> Number 0 refer to first device in the device tree node. The number increase if there are multiple devices with same name. For example, if there are 2 SPI devices, then it should be name as SPI_0 and SPI_1.
