from collections import namedtuple
from .components import *
from .blockdiagram import BlockDiagram
import copy


block = namedtuple('block', 'name, cls, path')

# convert class name to BLOCK name
# strip underscores and capitalize
def blockname(cls):
    return cls.__name__.strip('_').upper()


# print a progress bar
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printProgressBar (fraction, prefix='', suffix='', decimals=1, length=50, fill = '█', printEnd = "\r"):

    percent = ("{0:." + str(decimals) + "f}").format(fraction * 100)
    filledLength = int(length * fraction)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r{} |{}| {}% {}'.format(prefix, bar, percent, suffix), end = printEnd)


class BDSimState:

    """
    :ivar x: state vector
    :vartype x: np.ndarray
    :ivar T: maximum simulation time (seconds)
    :vartype T: float
    :ivar t: current simulation time (seconds)
    :vartype t: float
    :ivar fignum: number of next matplotlib figure to create
    :vartype fignum: int
    :ivar stop: reference to block wanting to stop simulation, else None
    :vartype stop: Block subclass
    :ivar checkfinite: halt simulation if any wire has inf or nan
    :vartype checkfinite: bool
    :ivar graphics: enable graphics
    :vartype graphics: bool
    """
    

    def __init__(self):

        self.x = None           # continuous state vector numpy.ndarray
        self.T = None           # maximum.BlockDiagram time
        self.t = None           # current time
        self.fignum = 0
        self.stop = None
        self.checkfinite = True

        self.debugger = True
        self.debug_stop = False
        self.t_stop = None  # time-based breakpoint

class BDSim:

    def __init__(self, verbose=False, **kwargs):
        """
        :param sysargs: process options from sys.argv, defaults to True
        :type sysargs: bool, optional
        :param graphics: enable graphics, defaults to True
        :type graphics: bool, optional
        :param animation: enable animation, defaults to False
        :type animation: bool, optional
        :param progress: enable progress bar, defaults to True
        :type progress: bool, optional
        :param debug: debug options, defaults to None
        :type debug: str, optional
        :param backend: matplotlib backend, defaults to 'Qt5Agg''
        :type backend: str, optional
        :param tiles: figure tile layout on monitor, defaults to '3x4'
        :type tiles: str, optional
        :raises ImportError: syntax error in block
        :return: parent object for blockdiagram simulation
        :rtype: BDSim
        
        Graphics display in all blocks can be disabled using the `graphics`
        option to the ``BlockDiagram`` instance.

        ===================  =========  ========  ===========================================
        Command line switch  Argument   Default   Behaviour
        ===================  =========  ========  ===========================================
        --nographics, -g     graphics   True      enable graphical display
        --animation, -a      animation  False     update graphics at each time step
        --noprogress, -p     progress   True      display simulation progress bar
        --backend BE         backend    'Qt5Agg'  matplotlib backend
        --tiles RxC, -t RxC  tiles      '3x4'     arrangement of figure tiles on the display
        --debug F, -d F      debug      ''        debug flag string
        ===================  =========  ========  ===========================================

        """
        # process command line and overall options
        self.options = self.get_options(**kwargs)

    def __str__(self):
        s = "BDSim: {} blocks in library\n".format(len(self.blocklibrary))
        for k, v in self.options.__dict__.items():
            s += '  {:s}: {}\n'.format(k, v)
        return s

    def done(self, bd, **kwargs):

        bd.done(**kwargs)

    def blockdiagram(self, name='main'):
        """
        Instantiate a new block diagram object.

        :param name: diagram name, defaults to 'main'
        :type name: str, optional
        :return: parent object for blockdiagram
        :rtype: BlockDiagram

        This object describes the connectivity of a set of blocks and wires.

        At instantiation it has additional attributes set:

            * a factory method for every block in the block library that returns
              an instance of the block and puts the block into this object's
              ``blocklist``
            * ``options`` a tuple of options

        :seealso: :func:`BlockDiagram`
        """
        
        # instantiate a new blockdiagram
        bd = BlockDiagram(name=name)

        def new_method(cls, bd):

            # return a wrapper for the block constructor that automatically
            # add the block to the diagram's blocklist
            def block_init_wrapper(self, *args, **kwargs):

                block = cls(*args, bd=bd, **kwargs)  # call __init__ on the block
                bd.add_block(block)
                return block
            
            # return a function that invokes the class constructor
            f = block_init_wrapper

            # move the __init__ docstring to the class to allow BLOCK.__doc__
            f.__doc__ = cls.__init__.__doc__  

            return f
        
        # bind the block constructors as new methods on this instance
        self.blockdict = {}
        for block in self.blocklibrary:
            # create a function to invoke the block's constructor
            f = new_method(block.cls, bd)
            
            # set a bound version of this function as an attribute of the instance
            # method = types.MethodType(new_method, bd)
            # setattr(bd, block.name, method)
            setattr(bd, block.name, f.__get__(self))
            
            # broken, should be by folder
            # blocktype = block.cls.__module__.split('.')[1]
            # if blocktype in self.blockdict:
            #     self.blockdict[blocktype].append(block.name)
            # else:
            #     self.blockdict[blocktype] = [block.name]

        # add a clone of the options
        bd.options = copy.copy(self.options)

        return bd

    def get_options(sysargs=True, **kwargs):
        
        # all switches and their default values
        defaults = {
            'backend': 'Qt5Agg',
            'tiles': '3x4',
            'graphics': True,
            'animation': False,
            'progress': True,
            'debug': ''
            }

            
        # function arguments override the command line options
        # provide a list of argument names and default values
        options = {}
        for option, default in defaults.items():
            if option in kwargs:
                # first priority is to constructor argument
                assert type(kwargs[option]) is type(default), 'passed argument ' + option + ' has wrong type'
                options[option] = kwargs[option]
            else:
                # drop through to the default value
                options[option] = default
        
        # stash these away
        options = defaults.copy().update(options)

        # setup debug parameters from single character codes
        debuglist = []
        if 'p' in options.debug:
            debuglist.append('propagate')
        if 's' in options.debug:
            debuglist.append('state')
        if 'd' in options.debug:
            debuglist.append('deriv')
        if 'i' in options.debug:
            debuglist.append('interactive')

        options.debuglist = debuglist

        return options
        