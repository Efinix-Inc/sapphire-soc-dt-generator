import os

DRIVER_FILE = os.path.join(os.path.relpath(os.path.dirname(__file__)), "../drivers.json")

# search keyword in soc.h
INTERRUPT = "IO_INTERRUPT"
PERIPHERAL = "CTRL "
IO_SIZE = "CTRL_SIZE"
FREQUENCY = "CLINT_HZ"
BASE_ADDR_PROP = "SYSTEM_BMB_PERIPHERAL_BMB "
# FPU = "FPU"
#MMU = "MMU"
MMU         = "EXT_M"
ATOMIC      = "EXT_A"
COMPRESS    = "EXT_C"
FPU         = "EXT_F"
DOUBLE      = "EXT_D"

ICACHE = "ICACHE"
DCACHE = "DCACHE"
CONTROLLER = ["PLIC", "CLINT", "RAM"]
PLIC = "PLIC"
CLINT = "CLINT"
SUPERVISOR = "SUPERVISOR "
memory_selection = 'int'
