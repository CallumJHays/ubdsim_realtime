from bdsim import BDSim
sim = BDSim()
bd = sim.blockdiagram()

clock = bd.clock(50, 'Hz')

sine = bd.WAVEFORM('sine')

sampled = bd.ADC(clock, sine)

bd.SCOPE(sampled)

bd.compile()

sim.run(bd, T=1)
sim.done(bd, block=True)