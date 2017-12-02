#!/usr/bin/env python
# -*- coding: utf-8 -*-

from manager import *
from lib import Const

if __name__ == '__main__':

    manager = Manager(0.001)
    manager.sendOrder(Const.ACT_ASK, 0.001)
