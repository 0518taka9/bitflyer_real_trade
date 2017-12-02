#!/usr/bin/env python
# -*- coding: utf-8 -*-
from math import sqrt
from lib import Const, Sequence
import time


#################################
#  バンドが拡大した際に買い、    ####
#  1αを下回ったら売る          #####
##################################

class BollingerAgent:
    N_CURVE = 9
    WIDTH = 100

    STATE_STAY = 0
    STATE_ASK = 1
    STATE_BID = 2

    def __init__(self, S, L, B, K, M, P, I, SLEEP, LOSSCUT):
        self.priceSeq = Sequence(L)
        self.averageCurve = Sequence(L)
        self.averageCurveShort = Sequence(L)
        self.bandWidth = Sequence(L)

        self.isActive = False
        self.state = self.STATE_STAY
        self.achieved = -1

        self.lose_count = 0
        self.inter_count = 0
        self.sleep_count = SLEEP

        self.price = 0

        self.S = S
        self.L = L
        self.B = B
        self.K = K
        self.M = M
        self.amountSeq = Sequence(P)
        self.I = I
        self.SLEEP = SLEEP
        self.LOSSCUT = LOSSCUT

    def drawerInfo(self):
        return (self.N_CURVE, self.WIDTH)

    def reset(self, lose):
        self.state = self.STATE_STAY
        self.lose_count += lose

        if self.lose_count >= 3:
            self.lose_count = 0
            self.sleep_count = 0

    def tick(self, price, amount):
        # 価格指標の計算
        pre_amount = self.amountSeq.summarize(lambda x: x)
        k = self.K * amount / (pre_amount + amount)
        self.price = self.price * (1 - k) + price * k
        self.amountSeq.append(amount)

        self.inter_count += 1

        if self.inter_count == self.I:
            self.inter_count = 0
            return self.decide()
        else:
            return (Const.ACT_STAY, None)

    def getPrice(self):
        return self.price

    def decide(self):
        price = self.getPrice()
        self.priceSeq.append(price)

        if self.sleep_count < self.SLEEP:
            self.sleep_count += 1

        self.isActive = (self.priceSeq.get(0) > 0 and self.sleep_count >= self.SLEEP)

        ################################
        #  各統計変数の計算      ########
        ################################

        s = self.priceSeq.summarize(lambda x: x)
        ss = self.priceSeq.summarize(lambda x: x * x)
        sd = sqrt((self.L * ss - s * s) / (self.L * (self.L - 1)))

        average = s / self.L
        average_s = sum(self.priceSeq.toArray()[-self.S:]) / self.S
        b = self.B * sd

        self.averageCurve.append(average)
        self.averageCurveShort.append(average_s)
        self.bandWidth.append(sd)

        ################################
        #  以下、行動の選択部分   ########
        ################################

        act = Const.ACT_STAY

        if not self.isActive:
            return (act, (
            price, average, average_s, average + b, average - b, average + b * 2, average - b * 2, average + b * 3,
            average - b * 3))

        state = self.state

        # 買い状態
        if state == self.STATE_ASK:
            if (self.achieved != -1 and price < average + self.achieved * b) or price < self.cut:
                self.state = self.STATE_STAY
                act = Const.ACT_BID

        # 売り状態
        if state == self.STATE_BID:
            if (self.achieved != -1 and price > average - self.achieved * b) or price > self.cut:
                self.state = self.STATE_STAY
                act = Const.ACT_ASK

        # 行動待機
        if state == self.STATE_STAY:
            if self.bandWidth.df(-2) < 0 and self.bandWidth.df(-1) > 0:
                if average_s > average * (1 + self.M):
                    self.state = self.STATE_ASK
                    act = Const.ACT_ASK
                    self.achieved = -1
                    self.cut = price * (1 - self.LOSSCUT)

                if average_s < average * (1 - self.M):
                    self.state = self.STATE_BID
                    act = Const.ACT_BID
                    self.achieved = -1
                    self.cut = price * (1 + self.LOSSCUT)

        # 価格更新
        if self.state == self.STATE_ASK:
            if price > average + b * 2:
                self.achieved = 2
            elif price > average + b:
                self.achieved = 1
            elif price > average:
                self.achieved = 0

        if self.state == self.STATE_BID:
            if price < average - b * 2:
                self.achieved = 2
            elif price < average - b:
                self.achieved = 1
            elif price < average:
                self.achieved = 0

        return (act, (
        price, average, average_s, average + b, average - b, average + b * 2, average - b * 2, average + b * 3,
        average - b * 3))
