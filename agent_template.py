#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib import Const, Sequence


class Agent:
    N_CURVE = 2  # 曲線の数
    WIDTH = 100  # 表示するデータ数

    STATE_STAY = 0
    STATE_ASK = 1
    STATE_BID = 2

    def __init__(self, L, I, LOSSCUT):
        """
        :param L: 
        :param I: decide()呼び出しの間隔 (20: 3s)
        :param double LOSSCUT: 
        """
        self.priceSeq = Sequence(L)

        self.isActive = False   # 価格情報が取得できているか
        self.state = self.STATE_STAY

        self.tick_count = 0    # tick()呼び出し回数のカウント

        self.L = L
        self.I = I
        self.LOSSCUT = LOSSCUT

    def drawerInfo(self):
        """
        グラフ描画用クラスDrawerに情報を渡す
        :return: 曲線数、幅
        """
        return (self.N_CURVE, self.WIDTH)

    def reset(self):
        """
        注文がリジェクトされた時などに呼び出される
        """
        self.state = self.STATE_STAY

    def tick(self, price, amount, active):
        """
        価格を元に何らかの指標を計算する。
        数回に一回(tick()の呼び出しはデフォルトで3秒ごと、10回ごとにすれば30秒に一回)
        decide()を呼び出し、Traderにアクションを返す。
        
        :param price: manager.tick()で設定した価格
        :param amount: manager.tick()で設定した取引量
        :param boolean active: 前回の注文が成功したか
        :return: decide()メソッド
        """
        self.price = price
        self.tick_count += 1

        # (I)回に1回decide()を呼び出す
        if self.tick_count == self.I:
            self.tick_count = 0
            return self.decide(active)

        else:
            return (Const.ACT_STAY, None)

    def getPrice(self):
        return self.price

    def decide(self, active):
        """
        :param active: 前回の注文が成功したか
        :return: アクション、データ(N_CURVE数)
        """
        price = self.getPrice()
        self.priceSeq.append(price)

        self.isActive = (self.priceSeq.get(0) > 0)

        # 統計変数の計算
        average = self.priceSeq.summarize(lambda x: x)

        # 行動決定
        act = Const.ACT_STAY

        if self.isActive and active:
            state = self.state

        # 買い状態
        if state == self.STATE_ASK:
            # if 利確or損切り条件 or price < self.cut:
            self.state = self.STATE_STAY
            act = Const.ACT_BID

            # 売り状態
        if state == self.STATE_BID:
            # if 利確or損切り条件 or price > self.cut:
            self.state = self.STATE_STAY
            act = Const.ACT_ASK

            # 行動待機
        if state == self.STATE_STAY:
            # if 買い条件:
            self.state = self.STATE_ASK
            act = Const.ACT_ASK
            self.cut = price * (1 - self.LOSSCUT)

            # if 売り条件:
            self.state = self.STATE_BID
            act = Const.ACT_BID
            self.cut = price * (1 + self.LOSSCUT)

        return (act, (price, average))
