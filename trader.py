#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import requests
from lib import *
from manager import Manager

"""
agentのアクションを受け取り、注文量などを計算してManagerに渡すなど、
トレードを管理する役割を担う。
self.waitごとにtickを実行する。
"""


class Trader:
    AVAILABLE = 0.8  # 残高の何％使うか
    CHALLENGE = 5  # 新規注文のチャレンジ回数
    LEVERAGE = 1    # レバレッジ

    def __init__(self, agent, losscut):
        """
        :param agent: エージェント
        :param double losscut: 
        """
        self.agent = agent
        self.manager = Manager(losscut)
        self.trade = 0
        self.wait = 300
        self.order_amount = 0  # 注文失敗時の注文量を保持
        self.last_action = time.time()
        self.tick_count = 0

        # APIで34本分のlogデータを取得してagentのSeqに格納
        values = []
        period = 300    # 何分足かを決める
        after = int(time.time() - period * 34)
        response = requests.get(
            "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?periods=" + str(period) + "&after=" + str(after))
        for value in response.json()["result"][str(period)]:
            # (終値, 平均値, 数量)
            values.append((value[4], (value[2] + value[3]) / 2, value[5]))

        values = values[:-1]

        for value in values:
            # for i in range(20):
            self.agent.tick(value[0], value[1], value[2], True)

        self.agent.reset()

    def reset(self):
        self.trade = 0
        self.agent.reset()

    def tick(self):
        """
        まずManager.tick()を呼び出して(平均)価格や数量の情報を受けとり、
        それをそのままagentに渡して、代わりにアクションを受け取る。
        売買アクションを受け取った際には、残高を元に発注数量を計算して
        ManagerのsendOrder()を呼び出し、注文を行う。
        """

        # (self.wait)秒に1回呼び出し
        if time.time() - self.last_action >= self.wait:
            self.last_action = time.time()

            # manager.tick()を呼び出し、終値、平均値、数量、ロスカット情報を取得
            (last, average, amount, losscut) = self.manager.tick()

            # ロスカットならSTAY状態に戻す
            if losscut:
                self.reset()

            # 注文に失敗していたら再び新規注文を試みる
            if self.order_amount > 0:
                # 新規注文
                if self.manager.sendOrder(self.order_act, self.order_amount) is not False:
                    self.order_amount = 0
                else:
                    print("Rejected!")
                    self.order_count -= 1
                    if self.order_count == 0:
                        self.order_amount = 0
                        self.reset()

            # agent.tick()を呼び出し、アクションを取得
            act = self.agent.tick(last, average, amount, self.order_amount == 0)

            # 残高を取得し購入可能数を計算
            inventory = self.manager.getInventory() * self.AVAILABLE * self.LEVERAGE
            self.jpy = inventory
            self.coin = inventory / average

            trade = 0  # 取引数量
            self.tick_count += 1

            if act == Const.ACT_ASK:
                if self.trade > 0:
                    # 買い戻し
                    trade = self.trade
                else:
                    # 買い入れ
                    trade = self.coin

            if act == Const.ACT_BID:
                if self.trade > 0:
                    # 売り戻し
                    trade = self.trade
                else:
                    # 売り入れ
                    trade = self.coin

            if trade > 0:
                # 新規注文
                if self.manager.sendOrder(act, trade) is not False:
                    # 注文成功
                    # 注文情報を表示
                    print("[Action: " + str(act) + " at Price: " + str(last) + " when: " + str(self.tick_count) + "]")

                    # 利確
                    if self.trade > 0:
                        if act == Const.ACT_ASK:
                            self.reset()

                        if act == Const.ACT_BID:
                            self.reset()
                    # 待機から買いor売り状態へ
                    else:
                        self.trade = trade
                        self.start_price = last
                else:
                    # 注文失敗
                    print("Rejected!")

                    # 失敗した注文の情報を保持
                    self.order_act = act
                    self.order_amount = trade

                    if self.trade > 0:
                        self.order_count = -1
                    else:
                        self.order_count = self.CHALLENGE

            print("Inventory: " + str(inventory))
            print("Trade: " + str(self.trade))
            print("Price: " + str(average))
            print("Amount: " + str(amount))
            print("Passed minutes: " + str(self.tick_count))
            # print("Time: " + str(time.time()))
            print("----------")
