
from typing import Optional


class BDSimState:

    """
    :ivar x: state vector
    :vartype x: np.ndarray
    :ivar T: maximum simulation time (seconds)
    :vartype T: float
    :ivar t: current simulation time (seconds)
    :vartype t: float
    :ivar fignum: number of next matplotlib figure to create
    :vartype fignum: int
    :ivar stop: reference to block wanting to stop simulation, else None
    :vartype stop: Block subclass
    :ivar checkfinite: halt simulation if any wire has inf or nan
    :vartype checkfinite: bool
    :ivar graphics: enable graphics
    :vartype graphics: bool
    """
    

    def __init__(self):

        self.x = None           # continuous state vector numpy.ndarray
        self.T: Optional[float] = None           # maximum.BlockDiagram time
        self.t: Optional[float] = None           # current time
        self.fignum = 0
        self.stop = None
        self.checkfinite = True

        self.debugger = True
        self.debug_stop = False
        self.t_stop = None  # time-based breakpoint
        self.count = 0
