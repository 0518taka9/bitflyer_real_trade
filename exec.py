#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import keyboard
from perfect_order_agent import *
from trader import Trader

PLAYING = 1
PAUSING = 0


def pause():
    global mode
    mode = 1 - mode


if __name__ == '__main__':

    agent = PerfectOrderAgent(34, 20)
    """
    :param L: 価格を保持する日数
    :param I: decide()呼び出しの間隔(traderのself.wait * I 秒)
    """

    trader = Trader(agent, 0.01)
    # keyboard.add_hotkey('esc', pause)

    global mode
    mode = PLAYING
    while True:
        if mode == PLAYING:
            trader.tick()
