#!/usr/bin/env python
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt


"""
定数用クラス
"""
class Const:
    ACT_STAY = 0
    ACT_ASK = 1
    ACT_BID = 2

    ACCEPTED = 1
    WAITING = 0
    REJECTED = -1
    LOSSCUT = -2


"""
系列の管理用クラス
直近の(size)日間の価格などのデータを保持
"""
class Sequence:
    def __init__(self, size):
        """
        :param size: 保持するデータの日数
        """
        self.size = size
        self.data = [0] * size
        self.top = 0

    def append(self, x):
        t = self.top
        self.data[t] = x
        self.top = (t + 1) % self.size

    def get(self, index):
        return self.data[(self.top + self.size + index) % self.size]

    def toArray(self):
        ar = []
        for i in range(self.size):
            ar.append(self.get(i))
        return ar

    def summarize(self, func):
        """
        ある関数に従ってデータを処理し足す
        :param func: 関数
        :return: 処理後の和
        """
        s = 0
        for i in range(self.size):
            s += func(self.data[i])

        return s

    def df(self, index):
        """
        差分を計算する
        :param index: インデックス
        :return: (index)とその直前の差分
        """
        return self.get(index) - self.get(index - 1)

    def ddf(self, index):
        """
        差分の差分を計算する
        :param index: インデックス
        :return: (index)とその直前の差分の差分
        """
        return self.df(index) - self.df(index - 1)


################################
#  グラフ描画用クラス      ########
################################

class Drawer:
    MARGIN = 0.001
    INF = 1000000000.0
    FOCUS = 0.2

    def __init__(self, info):
        (n_data, width) = info

        self.n_data = n_data
        self.width = width
        self.seq = []
        self.isActive = False

        x = range(width)
        lines = []

        for i in range(n_data):
            seq = Sequence(width)
            self.seq.append(seq)
            line, = plt.plot(x, seq.toArray())
            lines.append(line)

        self.lines = lines

    def sleep(self, t):
        plt.pause(t)

    def update(self, array):
        lower = self.INF
        upper = 0
        for i in range(self.n_data):
            self.seq[i].append(array[i])

            seq = self.seq[i].toArray()

            lower = min([lower, min(seq[-int(self.width * self.FOCUS):])])
            upper = max([upper, max(seq[-int(self.width * self.FOCUS):])])

            self.lines[i].set_ydata(seq)
            plt.draw()

        plt.ylim(lower * (1 - self.MARGIN), upper * (1 + self.MARGIN))

        self.isActive = (self.seq[0].get(0) > 0)
