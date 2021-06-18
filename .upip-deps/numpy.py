import typing
from typing import List, Tuple, Union
if 'TYPE_CHECKING' not in dir(typing):
    typing.TYPE_CHECKING = False


_int, _float, _bool = int, float, bool

if typing.TYPE_CHECKING:
    import ulab as np
else:
    from ulab import numpy as np
    import sys
    
    # this module
    mod = sys.modules[__name__]

    # essentially `from np import *`, which doesn't work in micropython
    for attr in dir(np):
        setattr(mod, attr, getattr(np, attr))

_DType = _int
_RClassKeyType = Union[slice, _int, _float, list, tuple, np.ndarray]

# this is a stripped down version of RClass (used by np.r_[...etc])
# it doesn't include support for string arguments as the first index element
class RClass:

    def __getitem__(self, key: Union[_RClassKeyType, Tuple[_RClassKeyType, ...]]):

        if not isinstance(key, tuple):
            key = (key,)

        objs: List[np.ndarray] = []
        scalars: List[_int] = []
        arraytypes: List[_DType] = []
        scalartypes: List[_DType] = []

        # these may get overridden in following loop
        axis = 0

        for idx, item in enumerate(key):
            scalar = False

            try:
                if isinstance(item, np.ndarray):
                    newobj = item

                elif isinstance(item, slice):
                    step = item.step
                    start = item.start
                    stop = item.stop
                    if start is None:
                        start = 0
                    if step is None:
                        step = 1
                    if isinstance(step, complex):
                        size = _int(abs(step))
                        newobj: np.ndarray = np.linspace(start, stop, num=size)
                    else:
                        newobj = np.arange(start, stop, step)

                # if is number
                elif isinstance(item, (_int, _float, _bool)):
                    newobj = np.array([item])
                    scalars.append(len(objs))
                    scalar = True
                    scalartypes.append(newobj.dtype())
                    
                else:
                    newobj = np.array(item)
                
            except TypeError:
                raise Exception("index object %s of type %s is not supported by r_[]" % (
                    str(item), type(item)))

            objs.append(newobj)
            if not scalar and isinstance(newobj, np.ndarray):
                arraytypes.append(newobj.dtype())

        # Ensure that scalars won't up-cast unless warranted
        final_dtype = min(arraytypes + scalartypes)
        for idx, obj in enumerate(objs):
            if obj.dtype != final_dtype:
                objs[idx] = np.array(objs[idx], dtype=final_dtype)

        return np.concatenate(tuple(objs), axis=axis)

    # this seems weird - not sure what it's for
    def __len__(self):
        return 0
        
r_ = RClass()
