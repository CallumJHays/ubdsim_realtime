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

# change these to your wifi details
WIFI_SSID = "TelstraDEA059"
WIFI_PASSWORD = "wr5ncwt798"

import network, utime
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print('connecting to network', WIFI_SSID, 'with password', WIFI_PASSWORD[0:3] + "*" * len(WIFI_PASSWORD[3:]))
if not wlan.isconnected():
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print('connecting failed. trying again in 1 second...')
        utime.sleep(1)
        print('available wifi networks are', [str(n[0]) for n in wlan.scan()])
        pass
print('Connected to Wifi Successfully! network config:', wlan.ifconfig())