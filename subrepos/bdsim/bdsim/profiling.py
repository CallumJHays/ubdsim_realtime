import utime


indent = ''
def timed(f):
    n = str(f).split(' ')
    myname = n[1] if len(n) > 1 else n

    def new_func(*args, **kwargs):
        global indent
        indent += '    '
        t = utime.ticks_us()

        result = f(*args, **kwargs)
        # TODO: account for this print time if nested
        print('{}.{}(*{}, **{}) took {}us'.format(indent,
              myname, args, kwargs, utime.ticks_diff(utime.ticks_us(), t)))

        indent = indent[:-4]
        return result
    return new_func
