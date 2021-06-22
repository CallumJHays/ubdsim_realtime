
from typing import Union
import socket

from micropython import const
import gc

from bdsim import BlockDiagram, Block, Plug, simulation_only
from bdsim.components import Clock
import bdsim_realtime

DATARECEIVER_ADDR = '192.168.0.11', 6404

Signal = Union[Block, Plug]

# first loop
# ADC_PIN = const(36)
# PWM_PIN = const(23) # This PWM is BROKEN on mine

# second loop
ADC_PIN = const(39)
PWM_PIN = const(22)

GPIO_V = 3.3

FREQ = 16
# offsets chosen after observing execution
ADC_OFFSET          = 0.0
CONTROLLER_OFFSET   = 0.015 # adc + gc.collect() execution takes <= 15ms
PWM_OFFSET          = 0.027 # controller execution takes <= 12ms
DATASENDER_OFFSET   = 0.039 # execution takes <= 12ms

R = 4.7e3
L = 47e-4 # +- 5%
C = 100e-6

# PID Controller Gains
DEFAULT_KP = 10
DEFAULT_KI = 2


def vc_rlc(bd: BlockDiagram, V_s: Signal, r: float, l: float, c: float):
    "Transfer function for voltage across a capacitor in an RLC circuit"
    return bd.LTI_SISO(1, [l * c, r * c, 1], V_s)

def discrete_pi_controller(bd: BlockDiagram, clock: Clock, p: float, i: float, *, min: float = -float('inf'), max=float('inf')):
    "Discrete PI Controller"
    p_term = bd.GAIN(p)
    i_term = bd.DINTEGRATOR(clock)

    input = bd.CLIP(
        bd.SUM('++', p_term, bd.GAIN(i, i_term)),
        min=min, max=max
    )

    def register_err(err: Signal):
        p_term[0] = err
        i_term[0] = err

    return input, register_err



def control_rlc(bd: BlockDiagram, reference: Signal, kp: float, ki: float):
    "Use A PI Controller to try and track the input reference signal with the voltage over the capacitor"

    adc = bd.ADC_ESP32(
        bd.clock(FREQ, offset=ADC_OFFSET, unit='Hz'),
        bit_width=12, v_max=3.6, pin=ADC_PIN)

    duty, register_err = discrete_pi_controller(bd,
        bd.clock(FREQ, offset=CONTROLLER_OFFSET, unit='Hz'),
        kp, ki, min=0, max=1)

    # max frequency allowable by ESP32 for smoothest output
    pwm_v = bd.PWM_ESP32(
        bd.clock(FREQ, offset=PWM_OFFSET, unit='Hz'),
        duty, freq=1000, v_on=3.3, pin=PWM_PIN)

    # with simulation_only:
    #     V_c = vc_rlc(pwm_v, R, L, C)

    err = bd.SUM('+-', reference, adc)
    register_err(err)

    return adc, err, duty, pwm_v

def run(kp: float, ki: float, type: str):
    gc.collect()
    clientsocket = socket.socket()
    print('connecting to ', DATARECEIVER_ADDR)
    clientsocket.connect(DATARECEIVER_ADDR) # connect to development laptop on LAN
    print('connected!')

    bd = BlockDiagram()

    if type == "step":
        target = bd.STEP(T=0)
    else:
        target = bd.WAVEFORM(type, offset=1)

    adc, err, duty, pwm_v = control_rlc(bd, target, kp, ki)

    print('handshaking with DATARECEIVER')
    bd.DATASENDER(
        clientsocket.makefile('rwb'),
        bd.TIME(), target, adc, err, duty, pwm_v,
        nin=6,
        clock=bd.clock(FREQ, offset=DATASENDER_OFFSET, unit='Hz'))
    print('handshake successful')
    clientsocket.setblocking(False)

    bdsim_realtime.run(bd, 5)

def run_default():
    run(DEFAULT_KP, DEFAULT_KI, "square")