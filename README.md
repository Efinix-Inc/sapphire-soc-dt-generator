# Sapphire-soc-dt-generator

A script to generate device tree for Linux and Zephyr based on Efinix RISCV Sapphire SoC configuration. A device tree is a hierachical data structure primarily used to describe hardware.

## Usage

```
usage: device_tree_generator.py [-h] [-d DIR] [-o OUTFILE] [-j]
                                soc board {linux,zephyr} ...

Device Tree Generator

positional arguments:
  soc                   path to soc.h
  board                 development kit name such as t120, ti60

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     Output generated output directory. By default is dts
  -o OUTFILE, --outfile OUTFILE
                        Override output filename. By default is sapphire.dtsi
  -j, --json            Save output file as json format

os:
  {linux,zephyr}
    linux               Target OS, Linux
    zephyr              Target OS, Zephyr
```

### Generate Device Tree

#### Linux

```bash
python3 device_tree_generator.py /path/to/soc.h ti180 linux
```



#### Zephyr

```bash
usage: device_tree_generator.py soc board zephyr [-h] [-em]
                                                 socname zephyrboard

positional arguments:
  socname           Custom soc name for Zephyr SoC dtsi
  zephyrboard       Zephyr board name

optional arguments:
  -h, --help        show this help message and exit
  -em, --extmemory  Use external memory. If no external memory enabled on the
                    SoC, internal memory will be used instead.
```

##### Example,

This is an example to generate device tree for Zephyr OS. It is based on Sapphire SoC and Ti180 board. The custom socname is `zoro` and the zephyrboard is `zero-one`.

###### Using on chip RAM

```bash
python3 device_tree_generator.py /path/to/soc.h ti180 zephyr zoro zero-one
```

###### Using external memory

```bash
python3 device_tree_generator.py /path/to/soc.h ti180 zephyr zoro zero-one -em
```