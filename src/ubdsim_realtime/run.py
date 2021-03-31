from ubdsim import BlockDiagram

def run(bd: BlockDiagram):
    print('stepres:', bd.evaluate([], 0))