"""
Transfer blocks:

- have inputs and outputs
- have state variables
- are a subclass of ``TransferBlock`` |rarr| ``Block``

"""
# The constructor of each class ``MyClass`` with a ``@block`` decorator becomes a method ``MYCLASS()`` of the BlockDiagram instance.


from typing import List, Optional

import numpy as np
import micropython

from .transfers import LTI_SS, siso_to_ss
from ..components import Clock, ClockedBlock, block
from ..profiling import timed

# ------------------------------------------------------------------------


@block
class ZOH(ClockedBlock):

    def __init__(self, clock, *inputs, x0=0, min=None, max=None, **kwargs):
        """
        :param ``*inputs``: Optional incoming connections
        :type ``*inputs``: Block or Plug
        :param x0: Initial state, defaults to 0
        :type x0: array_like, optional
        :param min: Minimum value of state, defaults to None
        :type min: float or array_like, optional
        :param max: Maximum value of state, defaults to None
        :type max: float or array_like, optional
        :param ``**kwargs``: common Block options
        :return: a ZOH block
        :rtype: Integrator instance

        Create a zero-order hold block.

        Output is the input at the previous clock time.  The state can be a scalar or a
        vector, this is given by the type of ``x0``.

        The minimum and maximum values can be:

            - a scalar, in which case the same value applies to every element of 
              the state vector, or
            - a vector, of the same shape as ``x0`` that applies elementwise to
              the state.

        .. note:: If input is not a scalar, ``x0`` must have the shape of the
            input signal.
        """
        self.type = 'sampler'
        super().__init__(nin=1, nout=1, inputs=inputs, clock=clock, **kwargs)
        
        self._x = x0
        # self.ndstates = len(self._x0)
        # print('nstates', self.nstates)

    @micropython.native
    def output(self, t=None):
        return [self._x]

    def tick(self, dt: float):
        self._x = self.inputs[0]

# ------------------------------------------------------------------------


@block
class DIntegrator(ClockedBlock):
    """
    :blockname:`INTEGRATOR`

    .. table::
       :align: left
    
    +------------+---------+---------+
    | inputs     | outputs |  states |
    +------------+---------+---------+
    | 1          | 1       | N       |
    +------------+---------+---------+
    | float,     | float,  |         | 
    | A(N,)      | A(N,)   |         |
    +------------+---------+---------+
    """

    def __init__(self, clock, *inputs, x0=0, gain=1.0, **kwargs):
        """
        :param ``*inputs``: Optional incoming connections
        :type ``*inputs``: Block or Plug
        :param x0: Initial state, defaults to 0
        :type x0: array_like, optional
        :param min: Minimum value of state, defaults to None
        :type min: float or array_like, optional
        :param max: Maximum value of state, defaults to None
        :type max: float or array_like, optional
        :param ``**kwargs``: common Block options
        :return: an INTEGRATOR block
        :rtype: Integrator instance

        Create an integrator block.

        Output is the time integral of the input.  The state can be a scalar or a
        vector, this is given by the type of ``x0``.

        The minimum and maximum values can be:

            - a scalar, in which case the same value applies to every element of 
              the state vector, or
            - a vector, of the same shape as ``x0`` that applies elementwise to
              the state.
        """
        self.type = 'discrete-integrator'
        super().__init__(nin=1, nout=1, inputs=inputs, clock=clock, **kwargs)

        # if isinstance(x0, (int, float)):
        #     self.ndstates = 1
        #     if min is None:
        #         min = -np.inf
        #     if max is None:
        #         max = np.inf

        # else:
        #     if isinstance(x0, np.ndarray):
        #         if x0.ndim > 1:
        #             raise ValueError('state must be a 1D vector')
        #     else:
        #         x0 = np.array(x0)

        #     self.ndstates = x0.shape()[0]
        #     if min is None:
        #         min = [-np.inf] * self.nstates
        #     elif len(min) != self.nstates:
        #         raise ValueError('minimum bound length must match x0')

        #     if max is None:
        #         max = [np.inf] * self.nstates
        #     elif len(max) != self.nstates:
        #         raise ValueError('maximum bound length must match x0')

        self._x = x0
        self.last_t = None
        # self.min = min
        # self.max = max
        self.gain = gain

    # @timed
    @micropython.native
    def output(self, t=None):
        return [self._x]

    # @timed
    @micropython.native
    def tick(self, dt: float):
        self._x += self.gain * dt * self.inputs[0]

# ------------------------------------------------------------------------ #

# @block
# class Z_LTI_SISO(ClockedBlock, TransferBlock):
#     pass

@block
class Discrete_LTI_SS(ClockedBlock, LTI_SS):
    """
    :blockname:`LTI_SS`

    .. table::
       :align: left

       +------------+---------+---------+
       | inputs     | outputs |  states |
       +------------+---------+---------+
       | 1          | 01      | nc      |
       +------------+---------+---------+
       | float,     | float,  |         |
       | A(nb,)     | A(nc,)  |         |
       +------------+---------+---------+
    """

    def __init__(self, clock: Clock, *inputs, x0=None, **kwargs):
        r"""
        :param ``*inputs``: Optional incoming connections
        :type ``*inputs``: Block or Plug
        :param N: numerator coefficients, defaults to 1
        :type N: array_like, optional
        :param D: denominator coefficients, defaults to [1, 1]
        :type D: array_like, optional
        :param x0: initial states, defaults to zero
        :type x0: array_like, optional
        :param ``**kwargs``: common Block options
        :return: A SCOPE block
        :rtype: LTI_SISO instance

        Create a discrete-time state-space LTI block (in the z domain).
        """

        ClockedBlock.__init__(self, clock, **kwargs)
        LTI_SS.__init__(self, *inputs, **kwargs)
        self.type = 'Discrete LTI SS'
        self.out: Optional[List[float]] = None

        if x0 is None:
            self._x0 = np.zeros((self.nstates,))
        else:
            self._x0 = x0
        self._output = list(self.C @ self._x0)
        self.ndstates = len(self._x0)

    def output(self, t=None):
        return self._output

    def deriv(self):
        raise NotImplementedError("Clocked blocks should not be derived.")

    def next(self):
        # bandaid for compilation stage
        if all(inp is None for inp in self.inputs):
            self.inputs = [0] * len(self.inputs)
        # difference equation
        new_x = self.A @ self._x + self.B @ np.array(self.inputs)
        # "hold" the state until next update
        self._output = list(self.C @ new_x)
        return new_x
        # ------------------------------------------------------------------------ #


@block
class Discrete_LTI_SISO(Discrete_LTI_SS):
    """
    :blockname:`LTI_SISO`

    .. table::
       :align: left

       +------------+---------+---------+
       | inputs     | outputs |  states |
       +------------+---------+---------+
       | 1          | 1       | n       |
       +------------+---------+---------+
       | float      | float   |         |
       +------------+---------+---------+

    """

    def __init__(self, clock: Clock, N=1, D=[1, 1], *inputs, x0=None, verbose=False, **kwargs):
        r"""
        :param N: numerator coefficients, defaults to 1
        :type N: array_like, optional
        :param D: denominator coefficients, defaults to [1, 1]
        :type D: array_like, optional
        :param ``*inputs``: Optional incoming connections
        :type ``*inputs``: Block or Plug
        :param x0: initial states, defaults to zero
        :type x0: array_like, optional
        :param ``**kwargs``: common Block options
        :return: A SCOPE block
        :rtype: LTI_SISO instance

        Create a SISO LTI block.

        Describes the dynamics of a single-input single-output (SISO) linear
        time invariant (LTI) system described by numerator and denominator
        polynomial coefficients.

        Coefficients are given in the order from highest order to zeroth
        order, ie. :math:`2s^2 - 4s +3` is ``[2, -4, 3]``.

        Only proper transfer functions, where order of numerator is less
        than denominator are allowed.

        The order of the states in ``x0`` is consistent with controller canonical
        form.

        Examples::

            LTI_SISO(N=[1, 2], D=[2, 3, -4])

        is the transfer function :math:`\frac{s+2}{2s^2+3s-4}`.
        """
        #print('in SISO constscutor')

        A, B, C = siso_to_ss(list(N), list(D), verbose)
        super().__init__(clock=clock, A=A, B=B, C=C, x0=x0, inputs=inputs, **kwargs)
        self.type = 'Discrete LTI SISO'


# if __name__ == "__main__":

#     import pathlib
#     import os.path

#     exec(open(os.path.join(pathlib.Path(
#         __file__).parent.absolute(), "test_transfers.py")).read())
