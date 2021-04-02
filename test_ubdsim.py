from ubdsim import BlockDiagram
import ubdsim_realtime

bd = BlockDiagram()

five = bd.CONSTANT(5)
six = bd.CONSTANT(6)
sum = bd.SUM('++', five, six)

bd.compile()
print('compiled')
ubdsim_realtime.run(bd)