
# indent = ''
# def timed(f):
#     myname = str(f).split(' ')[1]
#     def new_func(*args, **kwargs):
#         global indent
#         print('{}{}.{}(*{}, **{})'.format(indent, args[0], myname, args[1:], kwargs))
#         indent += '    '
#         t = utime.ticks_us()

#         def toc(mark: str, reset: bool = False):
#             nonlocal t
#             now = utime.ticks_us()
#             print('{} {:6.3f}ms @ {}'.format(
#                 indent,
#                 utime.ticks_diff(now, t) / 1000,
#                 mark
#             ))
#             if reset:
#                 t = now

#         result = f(*args, toc=toc, **kwargs)
#         toc('END')
#         indent = indent[:-4]
#         return result
#     return new_func