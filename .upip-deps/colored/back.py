#!/usr/bin/env python
# -*- coding: utf-8 -*-


from .colors import names


class back(object):

    ESC = '\x1b[48;5;'
    END = 'm'
    num = 0

for color in names:
    setattr(back, color, '{}{}{}'.format(back.ESC, back.num, back.END))
    back.num += 1
