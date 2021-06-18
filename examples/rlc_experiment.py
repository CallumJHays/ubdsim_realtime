
from typing import Union

from bdsim import BlockDiagram, Block, Plug, simulation_only
from bdsim.components import Clock
import bdsim_realtime
from micropython import const

bd = BlockDiagram()

Signal = Union[Block, Plug]

ADC_PIN = const(36)
PWM_PIN = const(23)
GPIO_V = 3.3

FREQ = 1
ADC_OFFSET          = 0 / FREQ / 3
CONTROLLER_OFFSET   = 1 / FREQ / 3
PWM_OFFSET          = 2 / FREQ / 3

R = 4.7e3
L = 100e-3
C = 100e-6


def vc_rlc(V_s: Signal, r: float, l: float, c: float):
    "Transfer function for voltage across a capacitor in an RLC circuit"
    return bd.LTI_SISO(1, [l * c, r * c, 1], V_s)

def discrete_pi_controller(clock: Clock, p: float, i: float, *, min: float = -float('inf'), max=float('inf')):
    "Discrete PI Controller"
    p_term = bd.GAIN(p)
    i_term = bd.DINTEGRATOR(clock)

    block = bd.CLIP(
        bd.SUM('++', p_term, bd.GAIN(i, i_term)),
        min=min, max=max
    )

    def register_err(err: Signal):
        p_term[0] = err
        i_term[0] = err

    return block, register_err



def control_rlc(reference: Signal):
    "Use A PI Controller to try and track the input reference signal with the voltage over the capacitor"

    adc = bd.ADC_ESP32(
        bd.clock(FREQ, offset=ADC_OFFSET, unit='Hz'),
        bit_width=12, v_max=3.6, pin=ADC_PIN)

    duty, register_err = discrete_pi_controller(
        bd.clock(FREQ, offset=CONTROLLER_OFFSET, unit='Hz'),
        20, 1, min=0, max=1)

    # max frequency allowable by ESP32 for smoothest output
    pwm_v = bd.PWM_ESP32(
        bd.clock(FREQ, offset=PWM_OFFSET, unit='Hz'),
        duty, freq=1000, v_on=3.3, pin=PWM_PIN)

    # with simulation_only:
    #     V_c = vc_rlc(pwm_v, R, L, C)

    err = bd.SUM('+-', reference, adc)
    register_err(err)

    return duty, adc



target = bd.STEP(T=0)
# target = bd.WAVEFORM('sine')

inp, adc = control_rlc(target)
# scope = bd.SCOPE(
#     labels=["Reference", "PWM", "ADC Reading", "Output"]
# )
# scope[0] = target
# scope[1] = inp
# scope[2] = adc
# scope[3] = output

bdsim_realtime.run(bd, 5)