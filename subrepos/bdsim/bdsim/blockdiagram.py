#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 21:43:18 2020

@author: corkep
"""
import colored
from ansitable import ANSITable, Column
import numpy as np
from typing import Callable, Dict, Type

from .state import BDSimState

from .components import *
from . import blocks as _




# ------------------------------------------------------------------------- #    

class BlockDiagram:
    """
    Block diagram class.  This object is the parent of all blocks and wires in 
    the system.
    
    :ivar wirelist: all wires in the diagram
    :vartype wirelist: list of Wire instances
    :ivar blocklist: all blocks in the diagram
    :vartype blocklist: list of Block subclass instances
    :ivar x: state vector
    :vartype x: np.ndarray
    :ivar compiled: diagram has successfully compiled
    :vartype compiled: bool
    :ivar blockcounter: unique counter for each block type
    :vartype blockcounter: Dict[str, int]
    :ivar blockdict: index of all blocks by category
    :vartype blockdict: dict of lists
    :ivar name: name of this diagram
    :vartype name: str
    """
    
    def __init__(self, name='main', state: BDSimState=None, **kwargs):


        self.wirelist = []      # list of all wires
        self.blocklist = []     # list of all blocks
        self.clocklist = []     # list of all clock sources
        self.compiled = False   # network has been compiled
        self.blockcounter = {}
        self.name = name
        self.nstates = 0
        self.ndstates = 0
        self.state = state
        self._issubsystem = False
        self._blockdict = {}
        self.options = None
        self.n_auto_sum = 0
        self.n_auto_prod = 0
        
        # map the block classes that have been loaded up
        # from their ALLCAPS name to their class object
        self.block_classes: Dict[str, Type[Block]] = {
            block_cls.__name__.upper(): block_cls
            for block_cls in blocklist
        }
        
    def __getitem__(self, b):
        return self._blockdict[b]

    def __len__(self):
        return len(self.blocklist)

    @property
    def issubsystem(self):
        return self._issubsystem
    
    def clock(self, *args, **kwargs):
        clock = Clock(*args, bd=self, **kwargs)
        self.clocklist.append(clock)
        return clock

    def add_block(self, block):
        block.id = len(self.blocklist)
        if block.name is None:
            i = self.blockcounter.get(block.type, 0)
            self.blockcounter[block.type] = i + 1
            block.name = "{:s}.{:d}".format(block.type, i)
        block.bd = self
        self.blocklist.append(block)  # add to the list of available blocks
        if block in self._blockdict:
            raise Warning("block name {} is not unique".format(block))
        self._blockdict[block.name] = block
        
    def add_wire(self, wire, name=None):
        wire.id = len(self.wirelist)
        wire.name = name
        return self.wirelist.append(wire)
    
    def __getattr__(self, name: str) -> Callable[..., Block]:
        assert name == name.upper(), "Block name must be in ALLCAPS"

        try:
            cls = self.block_classes[name]
            def init_wrapper(*args, **kwargs) -> Block:
                block = cls(*args, bd=self, **kwargs)
                self.add_block(block)
                return block

            return init_wrapper

        except:
            closest_3_blocknames = sorted(
                self.block_classes.keys(),
                key=lambda blockname: _levenshtein_distance(name, blockname)
            )[:3]
            
            raise Exception(
                'Could not find a BlockDiagram.attr or a block by the name "{}".\n'
                'Please check your spelling. The most similar block names are: {}.\n'
                'All known blocks are: {}\n'
                'If your block is missing, check that your block library has been correctly imported.'
                .format(name, closest_3_blocknames, list(self.block_classes.keys()))
            )
    
    def __str__(self):
        return 'BlockDiagram: {:s}'.format(self.name)
    
    def __repr__(self):
        return str(self) + " with {:d} blocks and {:d} wires".format(len(self.blocklist), len(self.wirelist))
        # for block in self.blocklist:
        #     s += str(block) + "\n"
        # s += "\n"
        # for wire in self.wirelist:
        #     s += str(wire) + "\n"
        # return s.lstrip("\n")
        
    def ls(self):
        for k,v in self.blockdict.items():
            print('{:12s}: '.format(k), ', '.join(v))
    
    def connect(self, start, *ends, name=None):
        
        """
        TODO:
            s.connect(out[3], in1[2], in2[3])  # one to many
            block[1] = SigGen()  # use setitem
            block[1] = SumJunction(block2[3], block3[4]) * Gain(value=2)
        """
                        
        # convert to default plug on port 0 if need be
        if isinstance(start, Block):
            start = Plug(start, 0)
        start.type = 'start'

        for end in ends:
            if isinstance(end, Block):
                end = Plug(end, 0)
            end.type = 'end'
                    
            if start.isslice and end.isslice:
                # we have a bundle of signals
                                
                assert start.width == end.width, 'slice wires must have same width'
                
                for (s,e) in zip(start.portlist, end.portlist):
                    wire = Wire( Plug(start.block, s, 'start'), Plug(end.block, e, 'end'), name)
                    self.add_wire(wire)
            elif start.isslice and not end.isslice:
                # bundle goint to a block
                assert start.width == start.block.nout, "bundle width doesn't match number of input ports"
                for inport,outport in enumerate(start.portlist):
                    wire = Wire( Plug(start.block, outport, 'start'), Plug(end.block, inport, 'end'), name)
                    self.add_wire(wire)
            else:
                wire = Wire(start, end, name)
                self.add_wire(wire)
        
    # ---------------------------------------------------------------------- #

    def compile(self, subsystem=False, doimport=True, report=False, verbose=True):
        """
        Compile the block diagram
        
        :param subsystem: importing a subsystems, defaults to False
        :type subsystem: bool, optional
        :param doimport: import subsystems, defaults to True
        :type doimport: bool, optional
        :raises RuntimeError: various block diagram errors
        :return: Compile status
        :rtype: bool
        
        Performs a number of operations:
            
            - Check sanity of block parameters
            - Recursively clone and import subsystems
            - Check for loops without dynamics
            - Check for inputs driven by more than one wire
            - Check for unconnected inputs and outputs
            - Link all output ports to outgoing wires
            - Link all input ports to incoming wires
            - Evaluate all blocks in the network

        """
        
        # name the elements
        self.nblocks = len(self.blocklist)
        self.nwires = len(self.wirelist)

        error = False
        
        self.nstates = 0
        self.ndstates = 0
        self.statenames = []
        self.dstatenames = []
        self.blocknames = {}
        
        if not subsystem and verbose:
            print('\nCompiling:')
        
        # process all subsystem imports
        # ssblocks = [b for b in self.blocklist if b.type == 'subsystem']
        # for b in ssblocks:
        #     print('  importing subsystem', b.name)
        #     if b.ssvar is not None:
        #         print('-- Wiring in subsystem', b, 'from module local variable ', b.ssvar)
        # self.blocklist, self.wirelist = self._subsystem_import(self, None)

        # check that wires all point to valid blocks
        # for w in self.wirelist:
        #     if w.start.block not in self.blocklist:
        #         raise RuntimeError("wire {w} starts at unreferenced block {}".format(w.start.block))
        #     if w.end.block not in self.blocklist:
        #         raise RuntimeError("wire {w} ends at unreferenced block {}".format(w.end.block))

        # run block specific checks
        for b in self.blocklist:
            b.check()

        # build a dictionary of all block names
        for b in self.blocklist:
            self.blocknames[b.name] = b
        
        # visit all stateful blocks
        for b in self.blocklist:
            if b.blockclass == 'transfer':
                self.nstates += b.nstates
                if b._state_names is not None:
                    assert len(b._state_names) == b.nstates, 'number of state names not consistent with number of states'
                    self.statenames.extend(b._state_names)
                else:
                    # create default state names
                    self.statenames.extend([b.name + 'x' + str(i) for i in range(0, b.nstates)])
            if b.blockclass == 'clocked':
                self.ndstates += b.nstates
                if b._state_names is not None:
                    assert len(b._state_names) == b.nstates, 'number of state names not consistent with number of states'
                    self.dstatenames.extend(b._state_names)
                else:
                    # create default state names
                    self.statenames.extend([b.name + 'X' + str(i) for i in range(0, b.nstates)])

        # initialize lists of input and output ports
        for b in self.blocklist:
            b.outports = [[] for i in range(0, b.nout)]
            b.inports = [None for i in range(0, b.nin)]
            b._parents = [None for i in range(0, b.nin)]
        
        # connect the source and destination blocks to each wire
        for w in self.wirelist:
            w.start.block.add_outport(w)
            w.end.block.add_inport(w)
            w.end.block._parents[w.end.port] = w.start.block
            
        # check connections every block 
        # for b in self.blocklist:
        #     # check all inputs are connected
        #     for port, connection in enumerate(b.inports):
        #         if connection is None:
        #             print('  ERROR: block {:s} input {:d} is not connected'.format(str(b), port))
        #             error = True
                    
        #     # check all outputs are connected
        #     for port,connections in enumerate(b.outports):
        #         if len(connections) == 0:
        #             print('  INFORMATION: block {:s} output {:d} is not connected'.format(str(b), port))
                    
        #     if b._inport_names is not None:
        #         assert len(b._inport_names) == b.nin, 'incorrect number of input names given: ' + str(b)
        #     if b._outport_names is not None:
        #         assert len(b._outport_names) == b.nout, 'incorrect number of output names given: ' + str(b)
        #     if b._state_names is not None:
        #         assert len(b._state_names) == b.nstates, 'incorrect number of state names given: ' + str(b)
                    
        # # check for cycles of function blocks
        # def _DFS(path):
        #     start = path[0]
        #     tail = path[-1]
        #     for outgoing in tail.outports:
        #         # for every port on this block
        #         for w in outgoing:
        #             dest = w.end.block
        #             if dest == start:
        #                 print('  ERROR: cycle found: ', ' - '.join([str(x) for x in path + [dest]]))
        #                 return True
        #             if dest.blockclass == 'function':
        #                 return _DFS(path + [dest]) # recurse
        #     return False

        # for b in self.blocklist:
        #     if b.blockclass == 'function':
        #         # do depth first search looking for a cycle
        #         if _DFS([b]):
        #             error = True

        # if error:
        #     if not subsystem:
        #         raise RuntimeError('could not compile system')

        # # create the execution plan/schedule
        # self.execution_plan()

        # # evaluate the network once to check out wire types
        # x = self.getstate0()

        # # for clock in self.clocklist:
        # #     clock._x = clock.getstate0()

        # if report:
        #     self.report()
        #     self.plan_print()

        # if not subsystem:
        #     try:
        #         self.evaluate_plan(x, 0.0, sinks=False)
        #     except RuntimeError as err:
        #         print('\nFrom compile: unrecoverable error in value propagation:', err)
        #         error = True
            
        if error:
            if not subsystem:
                raise RuntimeError('could not compile system')
        else:
            self.compiled = True
        
        return self.compiled

    def _subsystem_import(self, bd, sspath):
        
        blocks = []
        wires = bd.wirelist

        for b in bd.blocklist:
            # rename the block to include subsystem path
            if sspath is not None:
                b.name = sspath + '/' + b.name
            
            if b.type == 'subsystem':
                # deal with a subsystem
                #  - recurse to import it
                #  - add its blocks and wires to the set
                ssb, ssw = self._subsystem_import(b.subsystem, b.name)
                blocks.extend(ssb)
                wires.extend(ssw)

                # INPORT/OUTPORT blocks now become simple pass throughs
                # same number of inputs and outputs
                b.inport.nin = b.inport.nout
                b.outport.nout = b.outport.nin

                # modify the wiring, keep the INPORT/OUTPORT blocks but lose
                # the SUBSYSTEM blocks
                for w in bd.wirelist:
                    # for all wires at this level, find those that connect
                    # to the subsystem and tweak them
                    if w.start.block == b:
                        # SS output
                        w.start.block = b.outport
                    if w.end.block == b:
                        # SS input
                        w.end.block = b.inport

            else:
                # not a subsystem, just add the block to the list
                blocks.append(b)

        # systematically renumber all blocks and wires
        for i, b in enumerate(blocks):
            b.id = i
        for i, w in enumerate(wires):
            w.id = i
        return blocks, wires


    
    # ---------------------------------------------------------------------- #
    
    def evaluate_plan(self, x, t, checkfinite=True, debuglist=[], sinks=True):
        """
        Evaluate all blocks in the network

        :param x: state :type x: numpy.ndarray :param t: current time :type t:
        float :param checkfinite: check for Inf or Nan values in block outputs
        :type checkfinite: bool :return: state derivative :rtype: numpy.ndarray

        Performs the following steps:

        1. Partition the state vector ``x`` to all stateful blocks
        2. Execute the blocks in the order given by the ``plan``. The block
           outputs are "sent" to their connected inputs.

        Sink blocks are not executed here, but after completion their inputs
        will all be valid.
        """

        # TODO: don't copy outputs to inputs of next block, have inputs
        # pull the value from connected inputs

        try:
            self.simstate.t = t
        except:
            pass

        self.DEBUG('state', '>>>>>>>>> t=', t, ', x=', x, '>>>>>>>>>>>>>>>>')
        
        # reset all the blocks ready for the evalation
        self.reset()
        
        # split the state vector to stateful blocks
        for b in self.blocklist:
            if b.blockclass == 'transfer':
                x = b.setstate(x)

        # split the discrete state vector to clocked blocks
        for clock in self.clocklist:
            clock.setstate()

        self.DEBUG('propagate', 't={:.3f}'.format(t))

        for sequence, group in enumerate(self.plan):

            self.DEBUG('propagate', '---- sequence = ', sequence)

            for b in group:
                # ask the block for output, check for errors
                try:
                    out = b.output(t)
                except Exception as err:
                    # output method failed, report it
                    print('--Error at t={:f} when computing output of block {:s}'.format(t, str(b)))
                    print('  {}'.format(err))
                    print('  inputs were: ', b.inputs)
                    if b.nstates > 0:
                        print('  state was: ', b._x)

                    raise RuntimeError from None

                self.DEBUG('propagate', 'block {:s}: output = '.format(str(b),t) + str(out))

                # check that output is a list of correct length
                if not isinstance(out, list):
                    raise AssertionError("block {b} output {b} must be a list: {t}".format(b=b, t=type(out)))
                if len(out) != b.nout:
                    raise AssertionError("block {b} output {b} has incorrect length: {l} instead of {b}" \
                        .format(b=b, l=len(out), n=b.nout))

                # TODO check output validity once at the start
                
                # check it has no nan or inf values
                if checkfinite and isinstance(out, (int, float, np.ndarray)) and not np.isfinite(out).any():
                    raise RuntimeError("block {} output contains NaN".format(b))

                # send block outputs to all downstream connected blocks
                for (port, outwires) in enumerate(b.outports): # every port
                    value = out[port]
                    for w in outwires:     # every wire
                        
                        self.DEBUG('propagate', '  [', port, '] = ', value, ' --> ', w.end.block.name, '[', w.end.port, ']')
                        
                        # send value to wire
                        w.send(value)

                        # TODO send return status no longer needed
                        # TODO use common error handler in all cases above

        # gather the derivative
        YD = self.deriv()

        self.DEBUG('deriv', YD)


        return YD

    def execution_plan(self):
        """
        Create execution plan

        The plan is saved in the attribute ``plan`` and is a list
        ``[L0, L1, ... LN]`` where each ``Li`` is a list of blocks.  The blocks
        in the lists are executed sequentially, ie. all the blocks in ``L0``
        then all the blocks in ``L1`` etc.

        The plan ensures that the inputs of all blocks in ``Li`` have been
        previously computed.

        .. note::
            - The plan is essentially a dataflow graph. 
            - The blocks in list ``Li`` could potentially be executed in
              parallel.
            - Constant blocks and stateful blocks are all executed in ``L0``
            - The block attribute ``_sequence`` is ``i`` and indicates its
              execution order

        :seealso: :func:`plan_print`, :func:`plan_dotfile`
        """

        plan = []
        group = []
        for b in self.blocklist:
            b._sequence = None
            if b.blockclass in ('source', 'transfer', 'clocked'):
                b._sequence = 0
                group.append(b)
        plan.append(group)
        sequence = len(plan)

        while True:
            group = []
            for b in self.blocklist:
                if b._sequence is not None:
                    continue  # already has a sequence assigned
                
                if all([p._sequence < sequence if p._sequence is not None else False for p in b._parents]):
                    group.append(b)

            for b in group.copy():
                b._sequence = sequence
                if b.blockclass in ('sink',):
                    group.remove(b)
            if len(group) == 0:
                break
            plan.append(group)
            sequence += 1

        self.plan = plan
    
    def plan_print(self):
        """
        Display execution plan in tabular form

        :seealso: :func:`execution_plan`, :func:`plan_dotfile`
        """
        table = ANSITable(
            Column("Sequence"),
            Column("Blocks", colalign='<', headalign='^'),
            border='thin'
        )

        for sequence, group in enumerate(self.plan):
            table.row(sequence, ', '.join([str(b) for b in group]))
        
        table.print()

    def plan_dotfile(self, filename):
        """
        Write a GraphViz dot file representing the execution schedule
        
        :param file: Name of file to write to
        :type file: str

        The file can be processed using neato or dot::
            
            % dot -Tpng -o out.png dotfile.dot

        Display execution plan as a dataflow graph.

        :seealso: :func:`execution_plan`, :func:`plan_print`
        """

        if isinstance(filename, str):
            file = open(filename, 'w')
        else:
            file = filename
            
        header = r"""digraph G {

    graph [splines=ortho, rankdir=LR, splines=spline]
    node [shape=box]
    
    """
        file.write(header)

        for sequence, group in enumerate(self.plan):
            # for each execution group, place the blocks in a subgraph
            file.write('\tsubgraph step{:d} {{\n'.format(sequence))
            file.write('\t\trank=same;\n')

            for b in group:
                file.write('\t\t"{:s}"\n'.format(b.name))

            file.write('\t}\n\n')

        # connect them to their parents, except if a transfer block
        for b in self.blocklist:
            if not b.blockclass == 'transfer':
                for p in b._parents:
                    file.write('\t"{:s}" -> "{:s}"\n'.format(p.name, b.name))

        file.write('}\n')

    # ---------------------------------------------------------------------- #

    def _debugger(self, integrator=None):

        if self.t_stop is not None and self.t < self.t_stop:
            return

        self.t_stop = None
        while True:
            cmd = input("(bdsim, t={:.4f}) ".format(self.t))

            if len(cmd) == 0:
                continue

            if cmd[0] == 'p':
                # print variables
                for b in self.blocklist:
                    if b.nout > 0:
                        print(b.name, b.output(t=self.t))
            elif cmd[0] == 'i':
                print(integrator.status, integrator.step_size, integrator.nfev)
            elif cmd[0] == 's':
                # step
                break
            elif cmd[0] == 'c':
                # continue
                self.debug_stop = False
                break
            elif cmd[0] == 't':
                self.t_stop = float(cmd[1:])
                break
            elif cmd[0] in 'h?':
                print("p    print all outputs")
                print("i    print integrator status")
                print("s    single step")
                print("c    continue")
                print("t T  stop at or after time T")
                print("q    quit")

    # ---------------------------------------------------------------------- #

    def report(self):
        """
        Print a tabular report about the block diagram

        """
        # print all the blocks
        print('\nBlocks::\n')
        table = ANSITable(
                Column("id"),
                Column("name"),
                Column("nin"),
                Column("nout"),
                Column("nstate"),
                Column("ndstate"),
                Column("type", headalign="^", colalign="<"),
                border="thin"
            )
        for b in self.blocklist:
            table.row( b.id, str(b), b.nin, b.nout, b.nstates, b.ndstates, b.type)
        table.print()
        
        # print all the wires
        print('\nWires::\n')
        table = ANSITable(
                Column("id"),
                Column("from", headalign="^"),
                Column("to", headalign="^"),
                Column("description", headalign="^", colalign="<"),
                Column("type", headalign="^", colalign="<"),
                border="thin"
            )
        for w in self.wirelist:
            start = "{:d}[{:d}]".format(w.start.block.id, w.start.port)
            end = "{:d}[{:d}]".format(w.end.block.id, w.end.port)
            
            try:
                value = w.end.block.inputs[w.end.port]
                typ = type(value).__name__
                if isinstance(value, np.ndarray):
                    typ += ' {:s}'.format(str(value.shape()))
            except:
                typ = '??'
            table.row( w.id, start, end, w.fullname, typ)
        table.print()

        if self.ndstates > 0:
            # print all the clocked blocks
            print('\nClocked blocks::\n')
            table = ANSITable(
                    Column("id"),
                    Column("block"),
                    Column("clock"),
                    Column("period"),
                    Column("offset"),
                    border="thin"
                )
            for b in self.blocklist:
                if b.blockclass == 'clocked':
                    c = b.clock
                    table.row( b.id, str(b), c.name, c.T, c.offset)
            table.print()

        print('\nState variables:          {:d}'.format(self.nstates))
        print('Discrete state variables: {:d}'.format(self.ndstates))
        
        if not self.compiled:
            print('** System has not been compiled, or had a compile time error')

    def getstate0(self):
        # get the state from each stateful block
        parts = tuple(b.getstate0() for b in self.blocklist if b.blockclass == "transfer")
        return np.concatenate(parts) if parts else np.zeros(0)
                        
    def reset(self):
        """
        Reset conditions within every active block.  Most importantly, all
        inputs are marked as unknown.
        
        Invokes the `reset` method on all blocks.

        """
        for b in self.blocklist:
            b.reset()

    def step(self):
        """
        Tell all blocks to take action on new inputs.  Relevant to Sink
        blocks only since they have no output function to be called.
        """
        # TODO could be done by output method, even if no outputs
        
        for b in self.blocklist:
            b.step()
            self.simstate.count += 1

    def deriv(self):
        """
        Harvest derivatives from all blocks .
        """
        YD = np.zeros(0)
        for b in self.blocklist:
            if b.blockclass == 'transfer':
                yd = b.deriv().flatten()
                if not isinstance(yd, np.ndarray):
                    raise AssertionError("deriv: block {} did not return ndarray".format(b))
                if yd.ndim != 1 or yd.shape()[0] != b.nstates:
                    raise AssertionError("deriv: block {} returns wrong shape {}, should be ({},)".format(b, yd.shape(), b.nstates))
                YD = np.r_[YD, yd]
        return YD

    def start(self, **kwargs):
        """
        Inform all active blocks that.BlockDiagram is about to start.  Open files,
        initialize graphics, etc.
        
        Invokes the `start` method on all blocks.
        
        """
        # for c in self.clocklist:
        #     c.start(**kwargs)

        for b in self.blocklist:
            b.start(**kwargs)
                
    def initialstate(self):
        for b in self.blocklist:
            if b.blockclass in ('transfer', 'clocked'):
                b._x = b._x0

    def done(self, **kwargs):
        """
        Inform all active blocks that.BlockDiagram is complete.  Close files,
        graphics, etc.
        
        Invokes the `done` method on all blocks.
        
        """
        for b in self.blocklist:
            b.done(**kwargs)
        
    def dotfile(self, filename):
        """
        Write a GraphViz dot file representing the network.
        
        :param file: Name of file to write to
        :type file: str

        The file can be processed using neato or dot::
            
            % dot -Tpng -o out.png dotfile.dot

        """

        if isinstance(filename, str):
            file = open(filename, 'w')
        else:
            file = filename
            
        header = r"""digraph G {

    graph [splines=ortho, rankdir=LR]
    node [shape=box]
    
    """
        file.write(header)
        # add the blocks
        for b in self.blocklist:
            options = []
            if b.blockclass == "source":
                options.append("shape=box3d")
            elif b.blockclass == "sink":
                options.append("shape=folder")
            elif b.blockclass == "function":
                if b.type == 'gain':
                    options.append("shape=triangle")
                    options.append("orientation=-90")
                    options.append('label="{:g}"'.format(b.gain))
                elif b.type == 'sum':
                    options.append("shape=point")
            elif b.blockclass == 'transfer':
                options.append("shape=component")
            if b.pos is not None:
                options.append('pos="{:g},{:g}!"'.format(b.pos[0], b.pos[1]))
            options.append('xlabel=<<BR/><FONT POINT-SIZE="8" COLOR="blue">{:s}</FONT>>'.format(b.type))
            file.write('\t"{:s}" [{:s}]\n'.format(b.name, ', '.join(options)))
        
        # add the wires
        for w in self.wirelist:
            options = []
            #options.append('xlabel="{:s}"'.format(w.name))
            if w.end.block.type == 'sum':
                options.append('headlabel="{:s} "'.format(w.end.block.signs[w.end.port]))
            file.write('\t"{:s}" -> "{:s}" [{:s}]\n'.format(w.start.block.name, w.end.block.name, ', '.join(options)))

        file.write('}\n')
            
    def blockvalues(self):
        for b in self.blocklist:
            print('Block {:s}:'.format(b.name))
            print('  inputs:  ', b.inputs)
            print('  outputs: ', b.output(t=0))

    def DEBUG(self, debug, *args):
        if self.options and debug[0] in self.options.debug:
            print('DEBUG.{:s}: '.format(debug), *args)


# ripped from https://blog.paperspace.com/implementing-levenshtein-distance-word-autocomplete-autocorrect/
def _levenshtein_distance(token1: str, token2: str) -> float:
    distances = np.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2
        
    a = 0
    b = 0
    c = 0
    
    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if (token1[t1-1] == token2[t2-1]):
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]
                
                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return distances[len(token1)][len(token2)]