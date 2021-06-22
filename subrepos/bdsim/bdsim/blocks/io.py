"""
Define real-time i/o blocks for use in block diagrams.  These are blocks that:

- have inputs or outputs
- have no state variables
- are a subclass of ``SourceBlock`` or ``SinkBlock``

"""
# The constructor of each class ``MyClass`` with a ``@block`` decorator becomes a method ``MYCLASS()`` of the BlockDiagram instance.

from typing import Any, Optional, Tuple, Union
import numpy as np  # type: ignore

from bdsim.components import Block, Clock, ClockedBlock, Plug, SinkBlock, block
from bdsim.blocks.discrete import ZOH

"""
could have if/else chain here to define these classes according to the platform
or define each hardware in its own file, protected by if platform


Need some kind of synchronous update, evaluate the network, then wait for
sample time then update all analog blocks.  Perhaps a new kachunk method.
"""


@block
class ADC(ZOH):
    "A simulated model of an analog - digital converter"

    def __init__(
        self,
        clock: Clock,
        inp: Optional[Union[Block, Plug]] = None,
        *,
        bit_width: int,
        v_max: float,
        v_min: float = 0,
        pin: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(clock, *(inp,) if inp else (), **kwargs)
        self.v_min = v_min
        self.v_max = v_max
        self.v_range = v_max - v_min
        self.quant_n_idxs = 2 ** bit_width - 1
        self.quant_step_size = (v_max - v_min) / self.quant_n_idxs

    def tick(self, dt: float):
        inp: float = self.inputs[0]  # type: ignore

        res = None
        min_, max_ = self.v_min, self.v_max
        if inp < min_:
            res = min_
        elif inp > max_:
            res = max_
        else:
            # adc quantization
            step_idx = round((inp - min_) / self.quant_step_size)
            res = step_idx * self.quant_step_size + min_
        return res


@block
class PWM(ClockedBlock):
    """A simulated model of an ideal PWM generator.
    Takes a duty cycle as input and produces a PWM signal.
    """

    def __init__(
        self,
        clock: Clock,
        duty_cycle: Optional[Union[Block, Plug]] = None,
        *,
        freq: int,
        v_on: float,
        v_off: float = 0,
        duty0: int = 0,
        approximate: bool = True,
        pin: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(clock, nin=1, nout=1,  # type: ignore
                         inputs=(duty_cycle,) if duty_cycle else (), **kwargs)
        self.type = "pwm"
        self.times: Optional[tuple[float, float]] = None  # (last, next)
        self.T = 1 / freq

        # TODO: simulate slew rate
        # TODO: x0 represents offset? maybe a (last, next) tuple?
        self._x = duty0
        self.ndstates = 1
        self.v_on = v_on
        self.v_off = v_off
        self.approximate = approximate

    def output(self, t: float):
        if self.approximate:
            return [self._x * (self.v_on - self.v_off) + self.v_off]
        else:
            t_cycle = t % self.T
            t_on = self._x * self.T
            return [self.v_on if t_cycle <= t_on else self.v_off]

    def tick(self, dt: float):
        self._x = self.inputs[0]
