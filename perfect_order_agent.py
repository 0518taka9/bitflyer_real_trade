#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib import Const, Sequence


class PerfectOrderAgent:

    STATE_STAY = 0
    STATE_ASK = 1
    STATE_BID = 2

    BENEFIT = 0.004  # 利幅
    LOSSCUT = 0.002  # ロスカット
    CANDLESTICKS = 4  # エントリー条件(PO条件維持)
    CLOSE = 0.001  # エントリー条件(平均価格が短期移動平均線に近づく)

    def __init__(self, L, I):
        """
        :param L: 価格を保持する日数
        :param I: decide()呼び出しの間隔(traderのself.wait * I 秒)
        """
        self.priceSeq = Sequence(L)
        self.shortEMA = Sequence(L)  # 5EMA
        self.middleEMA = Sequence(L)  # 13EMA
        self.longEMA = Sequence(L)  # 34EMA

        self.isActive = False  # 価格情報が取得できているか
        self.state = self.STATE_STAY

        self.tick_count = 0  # tick()呼び出し回数のカウント

        self.L = L
        self.I = I
        # self.LOSSCUT = LOSSCUT

        self.first_day = True
        self.up_trend = 0
        self.down_trend = 0
        self.hold_price = 0

    # def drawerInfo(self):
    #     """
    #     グラフ描画用クラスDrawerに情報を渡す
    #     :return: 曲線数、幅
    #     """
    #     return (self.N_CURVE, self.WIDTH)

    def reset(self):
        """
       注文がリジェクトされた時などに呼び出される
       """
        self.state = self.STATE_STAY

    def tick(self, last, average, amount, active):
        """
        価格を元に何らかの指標を計算する。
        (I)回に一回(tick()の呼び出しはデフォルトで3秒ごと、10回ごとにすれば30秒に一回)
        decide()を呼び出し、Traderにアクションを返す。

        :param price: manager.tick()で設定した価格
        :param amount: manager.tick()で設定した取引量
        :param active: 前回の注文が成功したか
        :return: decide()
        """
        self.last = last
        self.average = average
        self.tick_count += 1

        # 買いor売り状態なら連続で呼び出し
        if self.state != self.STATE_STAY:
            return self.decide(active)

        # (I)回に1回decide()を呼び出す
        elif self.tick_count == self.I:
            return self.decide(active)

        else:
            return Const.ACT_STAY

    # def getPrice(self):
    #     return self.price

    def decide(self, active):
        """
        1分に1回呼び出し
        調整する箇所：
        EMAの日数、PO崩壊条件、利確の幅、
        エントリー条件(PO条件がローソク何本分続くか、価格と短期移動平均線の差)

        :param active: 前回の注文が成功したか
        :return: アクション
        """

        # 価格を取得し保持
        last = self.last
        average = self.average
        self.priceSeq.append(average)

        self.isActive = (self.priceSeq.get(0) > 0)

        # 1分目は移動平均に平均値を用いる
        if self.first_day:
            self.tick_count = 0

            short = average
            middle = average
            long_ = average

            self.shortEMA.append(short)
            self.middleEMA.append(middle)
            self.longEMA.append(long_)

            self.first_day = False

        # 2分目以降
        # 待機状態ならデータ保存&PO条件判断
        # 買いor売り状態なら、1分間に1回データ保存&PO条件判断
        elif self.state == self.STATE_STAY or self.tick_count == self.I:
            self.tick_count = 0

            # EMA(n) = EMA(n－1) + α ×｛当日価格 - EMA(n-1)｝
            # α（平滑化定数）＝2 / (n＋1）
            short = self.shortEMA.get(-1) + (2.0 / 6.0) * (average - self.shortEMA.get(-1))
            middle = self.middleEMA.get(-1) + (2.0 / 14.0) * (average - self.middleEMA.get(-1))
            long_ = self.longEMA.get(-1) + (2.0 / 35.0) * (average - self.longEMA.get(-1))

            self.shortEMA.append(short)
            self.middleEMA.append(middle)
            self.longEMA.append(long_)

            # パーフェクトオーダー条件(上昇トレンド)
            if short > middle and middle > long_ and self.middleEMA.df(-1) > 0 and self.longEMA.df(-1) > 0:
                self.up_trend += 1
                self.down_trend = 0
            # 5EMAと13EMAがクロスしたら崩壊
            elif short < middle:
                self.up_trend = 0

            # パーフェクトオーダー条件(下降トレンド)
            if short < middle and middle < long_ and self.middleEMA.df(-1) < 0 and self.longEMA.df(-1) < 0:
                self.down_trend += 1
                self.up_trend = 0
            # 5EMAと13EMAがクロスしたら崩壊
            elif short > middle:
                self.down_trend = 0

        # 行動決定
        act = Const.ACT_STAY
        if self.isActive and active:
            state = self.state

            # 買い状態
            if state == self.STATE_ASK:
                # PO条件が崩壊 or 損切り or 利益が保持価格の(BENEFIT)倍以上
                if self.up_trend == 0 or last < self.cut or last - self.hold_price > self.hold_price * self.BENEFIT:
                    self.up_trend = 0
                    self.state = self.STATE_STAY
                    act = Const.ACT_BID

            # 売り状態
            if state == self.STATE_BID:
                # PO条件が崩壊 or 損切り or 利益が保持価格の(BENEFIT)倍以上
                if self.down_trend == 0 or last > self.cut or self.hold_price - last > self.hold_price * self.BENEFIT:
                    self.down_trend = 0
                    self.state = self.STATE_STAY
                    act = Const.ACT_ASK

            # 待機状態
            if state == self.STATE_STAY:
                # (CANDLESTICKS)本のローソク足が経過してもPO条件(上昇)維持 and 平均価格が短期移動平均線に近づく(短期移動平均線を超えない)
                if self.up_trend >= self.CANDLESTICKS and average - self.shortEMA.get(-1) < average * self.CLOSE \
                        and self.middleEMA.get(-1) > average:
                    self.state = self.STATE_ASK
                    act = Const.ACT_ASK
                    self.cut = last * (1 - self.LOSSCUT)
                    self.hold_price = last

                # (CANDLESTICKS)本のローソク足が経過してもPO条件(下降)維持 and 平均価格が短期移動平均線に近づく(短期移動平均線を超えない)
                if self.down_trend >= self.CANDLESTICKS and self.shortEMA.get(-1) - average < average * self.CLOSE \
                        and self.middleEMA.get(-1) < average:
                    self.state = self.STATE_BID
                    act = Const.ACT_BID
                    self.cut = last * (1 + self.LOSSCUT)
                    self.hold_price = last

        return act
