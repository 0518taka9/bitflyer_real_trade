#!/usr/bin/env python
# -*- coding: utf-8 -*-

from manager import *
from lib import Const
import time
import requests

if __name__ == '__main__':
    hour = 2
    after = int(time.time() - 3600 * hour)  # (hour)時間分のlogデータ
    period = 86400  # (period)秒足のデータ
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?periods=86400&after=1483196400")

    for values in response.json()["result"][str(period)]:
        print values
    print len(response.json()["result"][str(period)])
    print time.time()
