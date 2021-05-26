from typing import Union
from ubdsim import BlockDiagram, Block, Plug
from ubdsim_realtime import run, simulation_only

Signal = Union[Block, Plug]

ADC_PIN = 0
PWM_PIN = 0
GPIO_V = 3.3

FREQ = 30
R = 1e3
L = 100e3
C = 1e-6

SMOOTHING_R = 100
SMOOTHING_C = 1e-3

bd = BlockDiagram()

def low_pass_filter(V_i: Signal, r: float, c: float):
    "Transfer function for a low-pass filter"
    return bd.LTI_SISO(
        1,
        (r * c, 1),
        V_i
    )

def vc_rlc(V_s: Signal, r: float, l: float, c: float):
    "Transfer function for voltage across a capacitor in an RLC circuit"
    return bd.LTI_SISO(
        1,
        (l * c, r * c, 1),
        V_s
    )

def control_rlc(reference: Signal):
    clock = bd.clock(T=FREQ, unit='Hz')

    ctrl = bd.Z_LTI_SISO()

    # max frequency allowable by ESP32 for best smoothest output
    pwm_v = bd.PROD(
        bd.PWM(clock, ctrl, freq=40e6, pin=PWM_PIN),
        bd.CONSTANT(GPIO_V)
    )

    with simulation_only:
        V_s = low_pass_filter(pwm_v, SMOOTHING_R, SMOOTHING_C)
        V_c = vc_rlc(V_s, R, L, C)

    adc = bd.ADC(clock, V_c, pin=ADC_PIN)
    err = bd.SUM('+-', reference, adc)

    ctrl[0] = err # connect err signal to controller
    
    return V_s, adc, V_c, err


def run_test():
    bd = BlockDiagram()

    target = bd.WAVEFORM('sine', freq=1)
    inp, actual, expected, err = control_rlc(target)
    bd.SCOPE(
        inp, actual, expected, err,
        nin=4,
        labels=["Control Input", "ADC Reading", "Projected Output", "Control Error"]
    )

    bd.compile()
    run(bd)