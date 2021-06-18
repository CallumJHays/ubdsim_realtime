
from machine import ADC, PWM, Pin, Timer, UART, freq

# set frequency to highest possible w/ ESP32
freq(240_000_000)

from micropython import const, schedule

# How often update() is called
OPERATING_FREQ = const(50) # 50hz
OPERATING_PERIOD = const(1000 // OPERATING_FREQ) # 20ms

PWM_FREQ = 1024

pwm_1 = PWM(Pin(23, Pin.OUT), freq=PWM_FREQ)
adc_1 = ADC(Pin(36, Pin.IN), atten=ADC.ATTN_11DB, width=ADC.WIDTH_12BIT)

pwm_2 = PWM(Pin(22, Pin.OUT), freq=PWM_FREQ)
adc_2 = ADC(Pin(39, Pin.IN))


from utime import ticks_us

# send data over the wire
# uart = UART(0, 115200)
# uart.init(115200, bits=9, parity=None, stop=1)

# This is where the action happens. Is run OPERATING_FREQ times per second
def update(_arg: None):
    
    # cycle the pwm
    duty = pwm_1.duty() + 4
    if duty > 300:
        duty = 0
    pwm_1.duty(duty)

    # print time, adc and duty reading
    print(ticks_us(), adc_1.read(), duty)

# Setup the timer to call update() every OPERATING_PERIOD
Timer(0).init(
    period=OPERATING_PERIOD,
    callback=lambda _: schedule(update, None)
)
Timer(0).deinit()
