"A good basic boot.py for general use"

from machine import freq

# set frequency to highest possible w/ ESP32
freq(240_000_000)

from micropython import opt_level, alloc_emergency_exception_buf

# interpreter/compiler optimization? not familiar with micropython byte code
# don't see a reason not to do this right now
opt_level(3)

# needed for helpful exceptions?
# https://docs.micropython.org/en/latest/library/micropython.html?highlight=schedule#micropython.alloc_emergency_exception_buf
alloc_emergency_exception_buf(100)
