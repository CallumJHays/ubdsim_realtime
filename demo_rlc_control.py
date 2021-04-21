from bdsim.bdsim.components import Plug
from typing import Union
from ubdsim import BlockDiagram, Block
from ubdsim_realtime import run, simulation_only

Signal = Union[Block, Plug]

V_CC_PIN = 0
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


def full_wave_rectifier(V_i: Signal):
    return bd.ABS(V_i)

def low_pass_filter(V_i: Signal, r: float, c: float):
    return bd.LTI_SISO(
        1,
        (r * c, 1),
        V_i
    )

def rlc_tf(V_s: Signal, r: float, l: float, c: float):
    return bd.LTI_SISO(
        1,
        (l * c, r * c, 1),
        V_s
    )

def control_rlc(reference: Signal):
    clock = bd.clock(T=1 / FREQ)

    ctrl = bd.Z_LTI_SISO()
    pwm = bd.PWM(clock, ctrl, freq=40e6) # max frequency for best smoothing with cheap capacitor

    # TODO: capacitor smoothing
    cap_input = 



    with simulation_only:
        V_i = bd.PROD("**", pwm, bd.CONSTANT())
        V_s = smoothed_rectifier(V_i, )
        V_c = rlc_tf(V_s, R, L, C)

    adc = bd.ADC(clock, V_c)
    err = bd.SUM('+-', reference, adc)

    pwm_out[0] = err # connect err signal to z-domain controller
    
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