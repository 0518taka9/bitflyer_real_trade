#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bitflyer import *
from lib import Sequence, Drawer
import time

API_KEY = ""
API_SECRET = ""
last_id = 0
last_action = time.time()
wait = 300
do_draw = 300 / wait
drawer_count = 0

N_CURVE = 4  # 曲線の数
WIDTH = 60   # 表示するデータ数

first_minute = True

L = 34      # データを保持する数
shortEMA = Sequence(L)  # 5EMA
middleEMA = Sequence(L)  # 13EMA
longEMA = Sequence(L)  # 34EMA

drawer = Drawer((N_CURVE, WIDTH))

if __name__ == '__main__':

    # APIを設定
    product = Product.BTC_FX
    api = BitflyerAPI(API_KEY, API_SECRET)

    while True:
        # (wait)秒に1回実行
        if time.time() - last_action >= wait:
            last_action = time.time()

            """
            ログデータをファイルに出力
            """
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

            # averageを計算
            if s_amount == 0:
                average = ticker["ltp"]
            else:
                average = s_price / s_amount

            # # (終値, 平均値, 数量, 高値, 安値)をlog.txtに出力
            # f = open("log.txt", "a")
            # f.write("(" + str(ticker["ltp"]) + ", " + str(average) + ", " + str(s_amount) + ", " + str(
            #     ticker["best_ask"]) + ", " + str(ticker["best_bid"]) + ")" + "\n")
            # f.close()

            """
            グラフ描画
            """
            drawer_count += 1

            # 1分間に1回描画する
            if drawer_count == do_draw:
                drawer_count = 0

                # 最初は移動平均に平均値を用いる
                if first_minute:
                    short = average
                    middle = average
                    long_ = average

                    shortEMA.append(short)
                    middleEMA.append(middle)
                    longEMA.append(long_)

                    first_minute = False
                else:
                    # 2回目以降
                    # EMA(n) = EMA(n－1) + α ×｛当日価格 - EMA(n-1)｝
                    # α（平滑化定数）＝2 / (n＋1）
                    short = shortEMA.get(-1) + (2.0 / 6.0) * (average - shortEMA.get(-1))
                    middle = middleEMA.get(-1) + (2.0 / 14.0) * (average - middleEMA.get(-1))
                    long_ = longEMA.get(-1) + (2.0 / 35.0) * (average - longEMA.get(-1))

                    shortEMA.append(short)
                    middleEMA.append(middle)
                    longEMA.append(long_)

                data = (average, short, middle, long_)

                drawer.update(data)
            drawer.sleep(0.001)
