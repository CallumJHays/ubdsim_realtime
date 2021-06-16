from bdsim.components import SinkBlock, SourceBlock, block, Block, Plug
from msgpack import dumps, loads, unpack
from io import IOBase
from typing import Any, List, Union
from os import PathLike
from abc import ABC


FilePath = Union[str, PathLike[str]]


@block
class DataSender(SinkBlock, ABC):

    class Error(Exception):
        pass

    def __init__(self, receiver: IOBase, labels: List[str], *inputs: Union[Block, Plug], **kwargs: Any):
        super().__init__(nin=len(labels), nout=0, *inputs, **kwargs)
        self.receiver = receiver

        # SYN -> server(receiver):SYN-ACK -> ACK (copy TCP scheme)
        receiver.write(dumps({
            'version': '0.0.1',
            'type': 'sender'
        }))

        syn_ack = loads(receiver.read())

        assert syn_ack['version'] == '0.0.1'

        receiver.write(dumps({
            'version': '0.0.1',
            'type': 'sender',
            'labels': labels
        }))

    def output(self, t: float):
        self.receiver.write(dumps(self.inputs))


@block
class DataReceiver(SourceBlock, ABC):
    # TODO: Should only work with bdsim-realtime

    def __init__(self, sender: IOBase, nout: int, **kwargs: Any):
        super().__init__(nin=0, nout=nout, **kwargs)

        self.sender = sender

        syn = loads(self.sender.read())
        assert syn['version'] == '0.0.1'

        ack = loads(self.sender.read())
        assert ack['version'] == '0.0.1'

    def output(self, t: float):
        # TODO: timeouts etc
        return loads(self.sender.read())


@block
class CSV(SinkBlock):

    def __init__(self, output: IOBase, nin: int, *inputs: Union[Block, Plug], **kwargs: Any):
        super().__init__(nin=nin, nout=0, *inputs, **kwargs)
        self.output = output

    def output(self, t: float):
        assert all(isinstance(inp, (int, float)) for inp in self.inputs)
        self.output.write(','.join(str(inp) for inp in self.inputs))
