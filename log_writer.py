#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bitflyer import *
import time

API_KEY = ""
API_SECRET = ""
last_id = 0
last_action = time.time()
wait = 60

if __name__ == '__main__':

    # APIを設定
    product = Product.BTC_FX
    api = BitflyerAPI(API_KEY, API_SECRET)

    while True:
        # (wait)秒に1回実行
        if time.time() - last_action >= wait:
            last_action = time.time()

            # tickerを取得
            ticker = api.get_ticker(product)

            # 約定履歴を取得
            trades = api.get_executions(product)

            s_price = 0  # 価格 * 取引数量の総和
            s_amount = 0  # 取引数量の総和

            for trade in trades:
                price = float(trade['price'])
                amount = float(trade['size'])
                trade_id = trade['id']

                # trade_idがlast_idならループを抜ける
                if last_id == trade_id:
                    break

                s_price += price * amount
                s_amount += amount

            # last_idを設定
            if len(trades) > 0:
                last_id = trades[0]['id']

            # priceを設定
            if s_amount == 0:
                average = ticker["ltp"]
            else:
                average = s_price / s_amount

            # (終値, 平均値, 数量, 高値, 安値)
            f = open("log.txt", "a")
            f.write("(" + str(ticker["ltp"]) + ", " + str(average) + ", " + str(s_amount) + ", " + str(ticker["best_ask"]) + ", " + str(ticker["best_bid"]) + ")" + "\n")
            f.close()
