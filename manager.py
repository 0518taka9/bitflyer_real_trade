#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bitflyer import *
from lib import Const

API_KEY = "Dq7bmkAroSi16ngpN9AT8d"
API_SECRET = "g7/cHV0gufOqoaBg40eNKnp0ig5CHyqPgxvqrkY16fc="


"""
APIのラッパー。注文など本番環境とのやり取りを担当する。
"""
class Manager:
    def __init__(self, LOSSCUT):
        """
        
        :param double LOSSCUT: 
        """
        self.product = Product.BTC_FX
        self.api = BitflyerAPI(API_KEY, API_SECRET)
        self.LOSSCUT = LOSSCUT
        self.act = Const.ACT_STAY
        self.last_id = 0

    def tick(self):
        """
        価格、数量、ロスカットを設定する。
        Traderのtickで呼び出される。
        ロスカット未実装
        :return: 終値、平均値、数量、ロスカット
        """

        # 約定履歴を取得
        trades = self.api.get_executions(self.product)

        s_price = 0     # 価格 * 取引数量の総和
        s_amount = 0    # 取引数量の総和

        for trade in trades:
            price = float(trade['price'])
            amount = float(trade['size'])
            trade_id = trade['id']

            # trade_idがlast_idならループを抜ける
            if self.last_id == trade_id:
                break

            s_price += price * amount
            s_amount += amount

        # last_idを設定
        if len(trades) > 0:
            self.last_id = trades[0]['id']

        # averageを計算
        if s_amount == 0:
            average = self.getLastPrice()
        else:
            average = s_price / s_amount

        # ロスカットを設定(未実装)
        losscut = False

        return (self.getLastPrice(), average, s_amount, losscut)

    def getLastPrice(self):
        """
        現在の終値を返す。
        :return: 現在の終値
        """
        return float(self.api.get_ticker(self.product)['ltp'])

    def getInventory(self):
        """
        残高を返す。
        :return: 残高
        """
        response = self.api.get_collateral()
        if response is False:
            sys.exit()

        return response['collateral']

    def roundPrice(self, price):
        return int(price)

    def roundAmount(self, amount):
        return round(int(amount / 0.000001) * 0.000001, 6)

    def sendOrder(self, action, amount):
        """
        本番用
        アクションと数量を渡し, 成行注文で注文を発行する。
        指値注文は未実装。
        Traderのtickで呼び出される。
        
        :param action: アクション(買い・売り・待機)
        :param amount: 注文量
        :return: 新規注文
        """

        side = ''

        if action == Const.ACT_ASK:
            side = Side.BUY
        if action == Const.ACT_BID:
            side = Side.SELL

        mode = OrderType.MARKET
        cond = TimeInForce.TIL_CANCELED
        rounded_amount = self.roundAmount(amount)

        order = ChildOrder(self.product, mode, side, rounded_amount, cond)

        # 新規注文を出す
        return self.api.send_child_order(order)
