import time

from ubdsim import BlockDiagram, TransferBlock, SourceBlock
from ubdsim.state import BDSimState

def run(bd: BlockDiagram, max_time=None):

    FPS_AV_FACTOR = 1 / 15  # smaller number averages over more frames
    FPS_AV_FACTOR_INV = 1 - FPS_AV_FACTOR
    fps = 30

    bd.T = max_time
    bd.state = BDSimState()

    for b in bd.blocklist:
        assert not isinstance(b, TransferBlock), \
            "Transfer blocks in realtime mode are not supported (yet)"

    sources = [b for b in bd.blocklist if isinstance(b, SourceBlock)]

    bd.start()
    start = time.time()
    print('started at', start)

    # if tuner:
    #     # needs to happen after bd.start() because the autogen'd block-names
    #     # are used internally
    #     tuner.setup(bd.gui_params, bd)

    while not bd.state.stop and (max_time is None or bd.t < max_time):
        bd.reset()

        last_t = bd.t
        bd.t = time.time() - start

        # propagate from source blocks onwards
        for b in sources:
            bd._propagate(b, t=bd.t)

        # check we have values for all
        for b in bd.blocklist:
            if b.nin > 0 and not b.done:
                raise RuntimeError(str(b) + ' has incomplete inputs')

        # update state, displays, etc
        bd.step()

        frequency = 1 / (bd.t - last_t) if last_t else fps

        # moving average formula
        fps = FPS_AV_FACTOR * frequency + FPS_AV_FACTOR_INV * fps
        print('FPS', fps)

