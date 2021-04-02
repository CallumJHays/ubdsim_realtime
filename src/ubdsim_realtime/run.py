import utime
from typing import Optional

from ubdsim import BlockDiagram, TransferBlock, SourceBlock
from ubdsim.state import BDSimState

def run(bd: BlockDiagram, max_time: Optional[float]=None):

    FPS_AV_FACTOR = 1 / 15  # smaller number averages over more frames
    FPS_AV_FACTOR_INV = 1 - FPS_AV_FACTOR
    fps = 30

    state = bd.state = BDSimState()
    state.T = max_time

    for b in bd.blocklist:
        assert not isinstance(b, TransferBlock), \
            "Transfer blocks in realtime mode are not supported (yet)"

    sources = [b for b in bd.blocklist if isinstance(b, SourceBlock)]

    bd.start()
    start = utime.time_ns() * 1e9
    print('started at', utime.time_ns())

    # if tuner:
    #     # needs to happen after bd.start() because the autogen'd block-names
    #     # are used internally
    #     tuner.setup(bd.gui_params, bd)

    # until its time to stop
    while not state.stop and (max_time is None or state.t < max_time):
        bd.reset()

        last_t = state.t
        state.t = (utime.time_ns() * 1e9) - start
        print(last_t, state.t)

        # propagate from source blocks onwards
        for b in sources:
            bd._propagate(b, t=state.t)

        # check we have values for all
        for b in bd.blocklist:
            if b.nin > 0 and not b.done:
                raise RuntimeError(str(b) + ' has incomplete inputs')

        # update state, displays, etc
        bd.step()

        # moving average f
        frequency = 1 / (state.t - last_t) if last_t else fps
        fps = FPS_AV_FACTOR * frequency + FPS_AV_FACTOR_INV * fps
        print('FPS', fps)

