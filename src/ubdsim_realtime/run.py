import time

from ubdsim import BlockDiagram, TransferBlock, SourceBlock
from ubdsim.state import BDSimState

def run(bd: BlockDiagram, max_time=None):

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

        # if tuner:
        #     tuner.update()
