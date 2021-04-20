from ubdsim import BlockDiagram
import ubdsim_realtime

FREQ = 30

def test():
    bd = BlockDiagram()

    clock = bd.clock(T=1 / FREQ)

    with ubdsim_realtime.simulation_only():
        five = bd.ADC(0, clock)
        six = bd.CONSTANT(6)
        sum = bd.SUM('++', five, six)

    bd.compile()
    ubdsim_realtime.run(bd)