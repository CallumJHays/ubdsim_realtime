
from machine import ADC, PWM, Pin, Timer, UART
from ubdsim import BlockDiagram
import ubdsim_realtime

bd = BlockDiagram()

clock = bd.clock(50, 'Hz')


uart = UART(0, 115200)
uart.init(115200, bits=9, parity=None, stop=1)
sender = bd.DATASENDER(uart, clock=clock)


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
