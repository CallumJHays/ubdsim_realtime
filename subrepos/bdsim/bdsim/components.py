#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Components of the simulation system, namely blocks, wires and plugs.
"""

from typing import Any, List, Optional
import numpy as np

mark_sim_only = False

class SimCtxManager:
    "All blocks defined within this context manager will not be run by realtime executors"
    def __init__(self):
        self.before = mark_sim_only

    def __enter__(self):
        global mark_sim_only
        mark_sim_only = True
    
    def __exit__(self):
        global mark_sim_only
        mark_sim_only = self.before

simulation_only = SimCtxManager()


class Struct(dict):
    """
    A dict like object that allows items to be added by attribute or by key.
    
    For example::
        
        >>> d = Struct('thing')
        >>> d.a = 1
        >>> d['b'] = 2
        >>> d.a
        1
        >>> d['a']
        1
        >>> d.b
        2
        >>> str(d)
        "thing {'a': 1, 'b': 2}"
    """
    
    def __init__(self, name='Struct'):
        super().__init__()
        self.name = name

    def __setattr__(self, name, value):
        # invoked by struct[name] = value
        if name in ['data', 'name']:
            super().__setattr__(name, value)
        else:
            self.data[name] = value
    
    def add(self, name, value):
        self.data[name] = value

    def __getattr__(self, name):
        return self.data[name]
        
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        def fmt(k, v, indent=0):
            if isinstance(v, Struct):
                s = '{:12s}| {:12s}\n'.format(k, type(v).__name__)
                for k, v in v.items():
                    s += fmt(k, v, indent + 1)
                return s
            elif isinstance(v, np.ndarray):
                s = '            > ' * indent + '{:12s}| {:12s}\n'.format(k, type(v).__name__ + ' ' + str(v.shape()))
            else:
                s = '            > ' * indent + '{:12s}| {:12s}\n'.format(k, type(v).__name__)
            return s

        s = ''
        for k, v in self.data.items():
            if k.startswith('_'):
                continue
            s += fmt(k, v)

        return self.name + ':\n' + s

class PriorityQ:

    def __init__(self):
        self.q = []

    def __len__(self):
        return len(self.q)

    def __str__(self):
        return "PriorityQ: len={}, first out {}".format(len(self), self.q[0])

    def push(self, value):
        self.q.append(value)

    def pop(self, dt=0):
        if len(self) == 0:
            return None, []
        self.q.sort(key=lambda x: x[0])

        qfirst = self.q.pop(0)
        t = qfirst[0]
        blocks = [qfirst[1]]
        while len(self.q) > 0 and self.q[0][0] < (t + dt):
            blocks.append(self.q.pop(0)[1])
        return t, blocks

    def pop_until(self, t):
        if len(self) == 0:
            return []

        self.q.sort(key=lambda x: x[0])
        i = 0
        while True:
            if self.q[i][0] > t:
                out = self.q[:i]
                self.q = self.q[i:]
                return out
            i += 1

class Wire:
    """
    Create a wire.
    
    :param start: Plug at the start of a wire, defaults to None
    :type start: Plug, optional
    :param end: Plug at the end of a wire, defaults to None
    :type end: Plug, optional
    :param name: Name of wire, defaults to None
    :type name: str, optional
    :return: A wire object
    :rtype: Wire

    A Wire object connects two block ports.  A Wire has a reference to the
    start and end ports.

    A wire records all the connections defined by the user.  At compile time
    wires are used to build inter-block references.
    
    Between two blocks, a wire can connect one or more ports, ie. it can connect
    a set of output ports on one block to a same sized set of input ports on 
    another block.
    """      
                
    def __init__(self, start=None, end=None, name=None):

        self.name = name
        self.id = None
        self.start = start
        self.end = end
        self.value = None
        self.type = None

    @property
    def info(self):
        """
        Interactive display of wire properties.
        
        Displays all attributes of the wire for debugging purposes.

        """
        print("wire:")
        for k,v in self.__dict__.items():
            print("  {:8s}{:s}".format(k+":", str(v)))
            
    def send(self, value, sinks=True):
        """
        Send a value to the port at end of this wire.
        
        :param value: A port value
        :type value: float, numpy.ndarray, etc.

        The value is sent to the input port connected to the end of this wire.
        """
        # dest is a Wire
        return self.end.block.setinput(self.end.port, value)
        
    def __repr__(self):
        """
        Display wire with name and connection details.
        
        :return: Long-form wire description
        :rtype: str
        
        String format::
            
            wire.5: d2goal[0] --> Kv[0]

        """
        return str(self) + ": " + self.fullname
    
    @property
    def fullname(self):
        """
        Display wire connection details.
        
        :return: Wire name
        :rtype: str

        String format::
            
            d2goal[0] --> Kv[0]
            
        """
        return "{:s}[{:d}] --> {:s}[{:d}]".format(str(self.start.block), self.start.port, str(self.end.block), self.end.port)
    
    def __str__(self):
        """
        Display wire name.
        
        :return: Wire name
        :rtype: str

        String format::
            
            wire.5
            
        """
        s = "wire."
        if self.name is not None:
            s += self.name
        elif self.id is not None:
            s += str(self.id)
        else:
            s += '??'
        return s

        
# ------------------------------------------------------------------------- # 

class Plug:
    """
    Create a plug.
    
    :param block: The block being plugged into
    :type block: Block
    :param port: The port on the block, defaults to 0
    :type port: int, optional
    :param type: 'start' or 'end', defaults to None
    :type type: str, optional
    :return: Plug object
    :rtype: Plug
    
    Plugs are the interface between a wire and block and have information
    about port number and wire end. Plugs are on the end of each wire, and connect a 
    Wire to a specific port on a Block.
    
    The ``type`` argument indicates if the ``Plug`` is at:
        - the start of a wire, ie. the port is an output port
        - the end of a wire, ie. the port is an input port
        
    A plug can specify a set of ports on a block.

    """

    def __init__(self, block, port=0, type=None):

        self.block = block
        self.port = port
        self.type = type  # start
        
    
    @property
    def isslice(self):
        """
        Test if port number is a slice.
        
        :return: Whether the port is a slice
        :rtype: bool

        Returns ``True`` if the port is a slice, eg. ``[0:3]``, and ``False``
        for a simple index, eg. ``[2]``.
        """
        return isinstance(self.port, slice)
    
    @property
    def portlist(self):
        """
        Return port numbers.
        
        :return: Port numbers
        :rtype: int or list of int
        
        If the port is a simple index, eg. ``[2]`` returns 2.
        
        If the port is a slice, eg. ``[0:3]``, returns [0, 1, 2].

        """
        if isinstance(self.port, slice):
            if self.port.step is None:
                return range(self.port.start, self.port.stop)
            else:
                return range(self.port.start, self.port.stop, self.port.step)
        else:
            return self.port

    @property
    def width(self):
        """
        Return number of ports connected.

        :return: Number of ports
        :rtype: int

        If the port is a simple index, eg. ``[2]`` returns 1.

        If the port is a slice, eg. ``[0:3]``, returns 3.
        """
        return len(self.portlist)

    def __rshift__(left, right):
        """
        Operator for implicit wiring.

        :param left: A plug to be wired from
        :type left: Plug
        :param right: A block or plug to be wired to
        :type right: Block or Plug
        :return: ``right``
        :rtype: Block or Plug

        Implements implicit wiring, where the left-hand operator is a Plug, for example::

            a = bike[2] >> bd.GAIN(3)

        will connect port 2 of ``bike`` to the input of the GAIN block.

        Note that::

           a = bike[2] >> func[1]

        will connect port 2 of ``bike`` to port 1 of ``func``, and port 1 of ``func``
        will be assigned to ``a``.  To specify a different outport port on ``func``
        we need to use parentheses::

            a = (bike[2] >> func[1])[0]

        which will connect port 2 of ``bike`` to port 1 of ``func``, and port 0 of ``func``
        will be assigned to ``a``.

        :seealso: Block.__mul__
        """

        # called for the cases:
        # block * block
        # block * plug
        s = left.block.bd
        #assert isinstance(right, Block), 'arguments to * must be blocks not ports (for now)'
        w = s.connect(left, right)  # add a wire
        #print('plug * ' + str(w))
        return right

    def __add__(self, other):
        return self.block.bd.SUM('++', self, other)

    def __sub__(self, other):
        return self.block.bd.SUM('+-', self, other)

    def __neg__(self):
        return self.block.bd.GAIN(-1, self)

    def __mul__(self, other):
        return self.block.bd.PROD('**', self, other)

    def __truediv__(self, other):
        return self.block.bd.PROD('*/', self, other)

    def __setitem__(self, port, src):
        """
        Convert a LHS block slice reference to a wire.

        :param port: Port number
        :type port: int
        :param src: the RHS
        :type src: Block or Plug

        Used to create a wired connection by assignment, for example::

            c = bd.CONSTANT(1)

            c[0] = x

        Ths method is invoked to create a wire from ``x`` to input port 0 of
        the constant block ``c``.
        """
        # b[port] = src
        # src --> b[port]
        print('Plug connecting', src, self, port)
        self.bd.connect(src, self[port])

    def __repr__(self):
        """
        Display plug details.

        :return: Plug description
        :rtype: str

        String format::

            bicycle.0[1]

        """
        return str(self.block) + "[" + str(self.port) + "]"

# ------------------------------------------------------------------------- #

clocklist = []

class Clock:

    def __init__(self, arg, unit, bd, offset=0, name=None):
        global clocklist
        if unit == 's':
            self.T = arg
        elif unit == 'ms':
            self.T = arg / 1000
        elif unit == 'Hz':
            self.T = 1 / arg

        self.offset = offset

        self.blocklist = []

        self.x = []  # discrete state vector numpy.ndarray
        self.t = []
        self.tick = 0

        self.name = "clock." + str(len(clocklist))

        clocklist.append(self)
        self.bd = bd

        # events happen at time t = kT + offset

    def add_block(self, block):
        self.blocklist.append(block)

    def __repr__(self):
        return str(self)

    def __str__(self):
        s = "{}: T={} sec".format(self.name, self.T)
        if self.offset != 0:
            s += ", offset={}".format(self.offset)
        s += ", clocking {} blocks".format(len(self.blocklist))
        return s

    def getstate0(self):
        return None # don't care - this is useless

    def getstate(self):
        # x = np.zeros(0)
        # for b in self.blocklist:
        #     # update dstate
        #     x = np.r_[x, b.next().flatten()]

        # return x
        return None

    def setstate(self):
        # x = self._x
        # for b in self.blocklist:
        #     x = b.setstate(x)  # send it to blocks
        return None

    def time(self, i):
        # return (math.floor((t - self.offset) / self.T) + 1) * self.T + self.offset
        # k = int((t - self.offset) / self.T + 0.5)
        return i * self.T + self.offset

    def savestate(self, t):
        # save clock state at time t
        self.t.append(t)
        self.x.append(self.getstate())
# ------------------------------------------------------------------------- #


blocklist = []


def block(cls):
    """
    Decorator for block classes

    :param cls: A block to be registered for the simulator
    :type cls: subclass of Block
    :return: the class
    :rtype: subclass of Block

    @block
    class MyBlock:

    The modules in ``./blocks`` uses the ``block`` decorator to declare
    that they are a block which will be made available as a method of the
    ``BlockDiagram`` instance.  The method name is a capitalized version of
    the class name.
    """

    if issubclass(cls, Block):
        blocklist.append(cls)  # append class to a global list
    else:
        raise ValueError('@block used on non Block subclass')
    return cls

# ------------------------------------------------------------------------- #

class Block:

    """
    Construct a new block object.

    :param name: Name of the block, defaults to None
    :type name: str, optional
    :param inames: Names of input ports, defaults to None
    :type inames: list of str, optional
    :param onames: Names of output ports, defaults to None
    :type onames: list of str, optional
    :param snames: Names of states, defaults to None
    :type snames: list of str, optional
    :param pos: Position of block on the canvas, defaults to None
    :type pos: 2-element tuple or list, optional
    :param bd: Parent block diagram, defaults to None
    :type bd: BlockDiagram, optional
    :param nin: Number of inputs, defaults to None
    :type nin: int, optional
    :param nout: Number of outputs, defaults to None
    :type nout: int, optional
    :param ``*inputs``: Optional incoming connections
    :type ``*inputs``: Block or Plug
    :param ``**kwargs``: Unknow arguments
    :return: A Block superclass
    :rtype: Block

    A block object is the superclass of all blocks in the simulation environment.

    This is the top-level initializer, and handles most options passed to
    the superclass initializer for each block in the library.

    """

    def __new__(cls, *args, bd=None, **kwargs):
        """
        Construct a new Block object.

        :param cls: The class to construct
        :type cls: class type
        :param *args: positional args passed to constructor
        :type *args: list
        :param **kwargs: keyword args passed to constructor
        :type **kwargs: dict
        :return: new Block instance
        :rtype: Block instance
        """
        block = super(Block, cls).__new__(cls)  # create a new instance

        # we overload setattr, so need to know whether it is being passed a port
        # name.  Add this attribute now to allow proper operation.
        setattr(block, 'portnames', []) # must be first, see __setattr__

        block.bd = bd
        block.nin = 0
        block.nout = 0
        block.nstates = 0
        block.ndstates = 0
        block._sequence = None
        return block

    def __init__(self, name=None, inames=None, onames=None, snames=None, pos=None, nin=None, nout=None, inputs=None, bd=None, **kwargs):
        # print('Block constructor, bd = ', bd)
        if name is not None:
            self.name_tex = name
            self.name = self._fixname(name)
        else:
            self.name_tex = None
            self.name = None
        self.pos = pos
        self.id = None
        self.out = []
        self.inputs = None
        self.updated = False
        self._inport_names = None
        self._outport_names = None
        self._state_names = None
        self.initd = True
        self.sim_only = mark_sim_only

        if nin is not None:
            self.nin = nin
        if nout is not None:
            self.nout = nout

        if inames is not None:
            self.inport_names(inames)
        if onames is not None:
            self.outport_names(onames)
        if snames is not None:
            self.state_names(snames)

        if inputs is not None and len(inputs) > 0:
            #assert len(inputs) == self.nin, 'Number of input connections must match number of inputs'
            for i, input in enumerate(inputs):
                self.bd.connect(input, Plug(self, port=i))

        if len(kwargs) > 0:
            print('WARNING: unused arguments', kwargs.keys())

    @property
    def info(self):
        """
        Interactive display of block properties.

        Displays all attributes of the block for debugging purposes.

        """
        print("block: " + type(self).__name__)
        for k,v in self.__dict__.items():
            if k != 'sim':
                print("  {:11s}{:s}".format(k+":", str(v)))

    @property
    def isclocked(self):
        return self._clocked

    # for use in unit testing
    def _eval(self, *inputs, t=None):
        """
        Evaluate a block for unit testing.
        
        :param *inputs: List of input port values
        :type *inputs: list
        :param t: Simulation time, defaults to None
        :type t: float, optional
        :return: Block output port values
        :rtype: list
        
        The output ports of the block are evaluated for a given set of input
        port values and simulation time. Input and output port values are treated
        as lists.
        
        Mostly used for making concise unit tests.

        """
        assert len(inputs) == self.nin, 'wrong number of inputs provided'
        self.inputs = inputs
        out = self.output(t=t)
        assert isinstance(out, list), 'result must be a list'
        assert len(out) == self.nout, 'result list is wrong length'
        return out

    def __getitem__(self, port):
        """
        Convert a block slice reference to a plug.

        :param port: Port number
        :type port: int
        :return: A port plug
        :rtype: Plug

        Invoked whenever a block is referenced as a slice, for example::

            c = bd.CONSTANT(1)

            bd.connect(x, c[0])
            bd.connect(c[0], x)

        In both cases ``c[0]`` is converted to a ``Plug`` by this method.
        """
        # block[i] is a plug object
        #print('getitem called', self, port)
        return Plug(self, port)

    def __setitem__(self, port, src):
        """
        Convert a LHS block slice reference to a wire.

        :param port: Port number
        :type port: int
        :param src: the RHS
        :type src: Block or Plug

        Used to create a wired connection by assignment, for example::

            c = bd.CONSTANT(1)

            c[0] = x

        Ths method is invoked to create a wire from ``x`` to port 0 of
        the constant block ``c``.
        """
        # b[port] = src
        # src --> b[port]
        #print('connecting', src, self, port)
        self.bd.connect(src, self[port])

    def __setattr__(self, name, value):
        """
        Convert a LHS block name reference to a wire.

        :param name: Port name
        :type port: str
        :param value: the RHS
        :type value: Block or Plug

        Used to create a wired connection by assignment, for example::

            c = bd.CONSTANT(1, inames=['u'])

            c.u = x

        Ths method is invoked to create a wire from ``x`` to port 'u' of
        the constant block ``c``.

        Notes:

            - this overloaded method handles all instances of ``setattr`` and
              implements normal functionality as well, only creating a wire
              if ``name`` is a known port name.
        """

        # b[port] = src
        # src --> b[port]
        # gets called for regular attribute settings, as well as for wiring

        if name in self.portnames:
            # we're doing wiring
            #print('in __setattr___', self, name, value)
            self.bd.connect(value, getattr(self, name))
        else:
            #print('in __setattr___', self, name, value)
            # regular case, add attribute to the instance's dictionary
            self.__dict__[name] = value

    def __rshift__(left, right):
        """
        Operator for implicit wiring.

        :param left: A block to be wired from
        :type left: Block
        :param right: A block or plugto be wired to
        :type right: Block or Plug
        :return: ``right``
        :rtype: Block or Plug

        Implements implicit wiring, for example::

            a = bd.CONSTANT(1) >> bd.GAIN(2)

        will connect the output of the CONSTANT block to the input of the
        GAIN block.  The result will be GAIN block, whose output in this case
        will be assigned to ``a``.

        Note that::

           a = bd.CONSTANT(1) >> func[1]

        will connect port 0 of CONSTANT to port 1 of ``func``, and port 1 of ``func``
        will be assigned to ``a``.  To specify a different outport port on ``func``
        we need to use parentheses::

            a = (bd.CONSTANT(1) >> func[1])[0]

        which will connect port 0 of CONSTANT ` to port 1 of ``func``, and port 0 of ``func``
        will be assigned to ``a``.

        :seealso: Plug.__rshift__

        """
        # called for the cases:
        # block * block
        # block * plug
        s = left.bd
        #assert isinstance(right, Block), 'arguments to * must be blocks not ports (for now)'
        w = s.connect(left, right)  # add a wire
        #print('block * ' + str(w))
        return right

        # make connection, return a plug

    def __add__(self, other):
        name = "autosum.{:d}".format(self.bd.n_auto_sum)
        self.bd.n_auto_sum += 1
        return self.bd.SUM('++', self, other, name=name)

    def __sub__(self, other):
        name = "autosum.{:d}".format(self.bd.n_auto_sum)
        self.bd.n_auto_sum += 1
        return self.bd.SUM('+-', self, other, name=name)

    def __neg__(self):
        return self >> self.bd.GAIN(-1)

    def __mul__(self, other):
        name = "autoprod.{:d}".format(self.bd.n_auto_prod)
        self.bd.n_auto_prod += 1
        return self.bd.PROD('**', self, other, name=name)


    def __truediv__(self, other):
        name = "autoprod.{:d}".format(self.bd.n_auto_prod)
        self.bd.n_auto_prod += 1
        return self.bd.PROD('*/', self, other, name=name)

    # TODO arithmetic with a constant, add a gain block or a constant block

    def __str__(self):
        if hasattr(self, 'name') and self.name is not None:
            return self.name
        else:
            return self.blockclass + '.??'

    def __repr__(self):
        return self.__str__()

    def _fixname(self, s):
        for frm, to in {'$':'', '\\':'', '{':'', '}':'', '^':'', '_':''}.items():
            s = s.replace(frm, to)
        return s

    def inport_names(self, names):
        """
        Set the names of block input ports.

        :param names: List of port names
        :type names: list of str

        Invoked by the ``inames`` argument to the Block constructor.

        The names can include LaTeX math markup.  The LaTeX version is used
        where appropriate, but the port names are a de-LaTeXd version of the
        given string with backslash, caret, braces and dollar signs
        removed.
        """
        self._inport_names = names

        for port, name in enumerate(names):
            fn = self._fixname(name)
            setattr(self, fn, self[port])
            self.portnames.append(fn)

    def outport_names(self, names):
        """
        Set the names of block output ports.

        :param names: List of port names
        :type names: list of str

        Invoked by the ``onames`` argument to the Block constructor.

        The names can include LaTeX math markup.  The LaTeX version is used
        where appropriate, but the port names are a de-LaTeXd version of the
        given string with backslash, caret, braces and dollar signs
        removed.

        """
        self._outport_names = names
        for port, name in enumerate(names):
            fn = self._fixname(name)
            setattr(self, fn, self[port])
            self.portnames.append(fn)

    def state_names(self, names):
        self._state_names = names

    def sourcename(self, port):
        """
        Get the name of output port driving this input port.

        :param port: Input port
        :type port: int
        :return: Port name
        :rtype: str

        Return the name of the output port that drives the specified input
        port. The name can be:

            - a LaTeX string if provided
            - block name with port number given in square brackets.  The block
              name will the one optionally assigned by the user using the ``name``
              keyword, otherwise a systematic default name.

        :seealso: outport_names

        """

        w = self.inports[port]
        if w.name is not None:
            return w.name
        src = w.start.block
        srcp = w.start.port
        if src._outport_names is not None:
            return src._outport_names[srcp]
        return str(w.start)

    # @property
    # def fullname(self):
    #     return self.blockclass + "." + str(self)

    def reset(self):
        if self.nin > 0:
            self.inputs = [None] * self.nin
        self.updated = False

    def add_outport(self, w):
        port = w.start.port
        assert port < len(self.outports), 'port number too big'
        self.outports[port].append(w)

    def add_inport(self, w):
        port = w.end.port
        assert self.inports[port] is None, 'attempting to connect second wire to an input'
        self.inports[port] = w

    def setinput(self, port, value):
        """
        Receive input from a wire

        :param self: Block to be updated
        :type wire: Block
        :param port: Input port to be updated
        :type port: int
        :param value: Input value
        :type val: any
        """
        # stash it away
        self.inputs[port] = value


    def setinputs(self, *pos):
        assert len(pos) == self.nin, 'mismatch in number of inputs'
        self.reset()
        for i, val in enumerate(pos):
            self.inputs[i] = val

    def start(self, **kwargs):  # begin of a simulation
        pass

    def check(self):  # check validity of block parameters at start
        assert self.nin > 0 or self.nout > 0, 'no inputs or outputs specified'
        assert hasattr(self, 'initd') and self.initd, 'Block superclass not initalized. was super().__init__ called?'

    def done(self, **kwargs):  # end of simulation
        pass

    def step(self):  # valid
        pass

    def output(self, t: float) -> Optional[List[Any]]:
        ...

    def savefig(self, *pos, **kwargs):
        pass

class SinkBlock(Block):
    """
    A SinkBlock is a subclass of Block that represents a block that has inputs
    but no outputs. Typically used to save data to a variable, file or 
    graphics.
    """
    blockclass='sink'

    def __init__(self, **kwargs):
        # print('Sink constructor')
        super().__init__(**kwargs)
        self.nout = 0
        self.nstates = 0



class SourceBlock(Block):
    """
    A SourceBlock is a subclass of Block that represents a block that has outputs
    but no inputs.  Its output is a function of parameters and time.
    """
    blockclass = 'source'

    def __init__(self, **kwargs):
        # print('Source constructor')
        super().__init__(**kwargs)
        self.nin = 0
        self.nstates = 0


class TransferBlock(Block):
    """
    A TransferBlock is a subclass of Block that represents a block with inputs
    outputs and states. Typically used to describe a continuous time dynamic
    system, either linear or nonlinear.
    """
    blockclass = 'transfer'

    def __init__(self, **kwargs):
        # print('Transfer constructor')
        super().__init__(**kwargs)
        self._x = self._x0

    def reset(self):
        super().reset()
        self._x = self._x0
        # return self._x

    def setstate(self, x):
        x = np.array(x)
        self._x = x[:self.nstates]  # take as much state vector as we need
        return x[self.nstates:]     # return the rest

    # def getstate0(self):
    #     return self._x0

    def check(self):
        assert len(self._x0) == self.nstates, 'incorrect length for initial state'
        assert self.nin > 0 or self.nout > 0, 'no inputs or outputs specified'


class FunctionBlock(Block):
    """
    A FunctionBlock is a subclass of Block that represents a block that has inputs
    and outputs but no state variables.  Typically used to describe operations
    such as gain, summation or various mappings.
    """
    blockclass = 'function'

    def __init__(self, **kwargs):
        # print('Function constructor')
        super().__init__(**kwargs)
        self.nstates = 0


class SubsystemBlock(Block):
    """
    A Function is a subclass of Block that represents a block that has inputs
    and outputs but no state variables.  Typically used to describe operations
    such as gain, summation or various mappings.
    """
    blockclass = 'subsystem'

    def __init__(self, **kwargs):
        # print('Subsystem constructor')
        super().__init__(**kwargs)
        self.nstates = 0

class ClockedBlock(Block):
    """
    A ClockedBlock is a subclass of Block that represents a block with inputs
    outputs and discrete states. Typically used to describe a discrete time dynamic
    system, either linear or nonlinear.
    """
    blockclass = 'clocked'

    def __init__(self, clock=None, **kwargs):
        # print('Clocked constructor')
        super().__init__(**kwargs)
        assert clock is not None, 'clocked block must have a clock'
        self._clocked = True
        self.clock = clock
        clock.add_block(self)

    def reset(self):
        super().reset()
        # self._x = self._x0
        # return self._x

    def setstate(self, x):
        # self._x = x[:self.ndstates]  # take as much state vector as we need
        # # print('** set block state to ', self._x)
        # return x[self.ndstates:]     # return the rest
        return None

    def getstate0(self):
        return self._x0

    def check(self):
        pass
        # assert len(self._x0) == self.ndstates, 'incorrect length for initial state'

        # assert self.nin > 0 or self.nout > 0, 'no inputs or outputs specified'
        # self._x = self._x0

    def tick(self, dt: float) -> None:
        raise NotImplementedError()


# c = Clock(5)
# c1 = Clock(5, 2)

# print(c, c1)
# print(c.next(0), c1.next(0))

