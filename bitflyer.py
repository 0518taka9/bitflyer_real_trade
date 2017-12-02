#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import hmac
import sys
import time

import requests
from enum import Enum


class ChildOrder:
    def __init__(self, product_code, child_order_type,
                 side, size, time_in_force):
        self.product_code = product_code
        self.child_order_type = child_order_type
        self.side = side
        self.size = size
        self.time_in_force = time_in_force

    def to_body(self):
        args = {
            "product_code": self.product_code,
            "child_order_type": self.child_order_type,
            "side": self.side,
            "size": self.size,
            "time_in_force": self.time_in_force
        }

        return args


class Product(Enum):
    BTC_JPY = "BTC_JPY"
    BTC_FX = "FX_BTC_JPY"
    ECH_BTC = "ETH_BTC"


class OrderType(Enum):
    LIMIT = "LIMIT"  # 指値注文
    MARKET = "MARKET"  # 成行注文


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    TIL_CANCELED = "GTC"  # 注文が約定するかキャンセルされるまで有効
    IMMEDIATE_OR_CANCEL = "IOC"  # 指定した価格かそれよりも有利な価格で即時に一部あるいは全部を約定させ、約定しなかった注文数量をキャンセル
    FILL_OR_KILL = "FOK"  # 発注の全数量が即座に約定しない場合当該注文をキャンセル


class BitflyerAPI:
    BASE_URL = "https://api.bitflyer.jp{0}"
    ERROR_LIMIT = 3
    SLEEP = 0.5

    api_key = ""
    api_secret = ""
    error_count = 0

    def __init__(self, api_key, api_secret):
        self.session = requests.session()
        self.api_key = api_key
        self.api_secret = api_secret

    # 板情報を取得
    def get_board(self, product):
        params = {"product_code": product}
        response = self.get_request("/v1/getboard", params=params).json()
        return response

    # Tickerを取得
    def get_ticker(self, product):
        params = {"product_code": product}
        response = self.get_request("/v1/getticker", params=params).json()
        return response

    # 約定履歴
    def get_executions(self, product):
        params = {"product_code": product}
        response = self.get_request("/v1/getexecutions", params=params).json()
        return response

    # 資産残高を取得
    def get_balance(self):
        method = "GET"
        endpoint = "/v1/me/getbalance"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 証拠金の状態を取得
    def get_collateral(self):
        method = "GET"
        endpoint = "/v1/me/getcollateral"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 新規注文を出す
    def send_child_order(self, order):
        method = "POST"
        endpoint = "/v1/me/sendchildorder"
        body = order.to_body().__str__()
        print body
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.post_request(endpoint=endpoint, params=body, headers=headers)
        if response is False:
            return False
        else:
            return response.json()

    # Private API用のヘッダーを作成
    def create_private_header(self, method, endpoint, body):
        if self.api_key and self.api_secret:
            access_timestamp = str(time.time())
            api_secret = str.encode(self.api_secret)
            text = str.encode(access_timestamp + method + endpoint + body)
            access_sign = hmac.new(api_secret,
                                   text,
                                   hashlib.sha256).hexdigest()
            auth_header = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-TIMESTAMP": access_timestamp,
                "ACCESS-SIGN": access_sign,
                "Content-Type": "application/json"
            }
            return auth_header
        else:
            sys.exit()

    # GETメソッド用
    def get_request(self, endpoint, params=None, headers=None):
        url = self.BASE_URL.format(endpoint)
        while self.error_count < self.ERROR_LIMIT:
            try:
                response = self.session.get(url, params=params, headers=headers)
                if not (response.status_code == 200 or response.status_code == 404):
                    print(response)
                    self.error_count += 1
                    time.sleep(self.SLEEP)
                    continue
                self.error_count = 0
                return response
            except Exception as e:
                print(e)
                self.error_count += 1
                time.sleep(self.SLEEP)
                continue

        self.error_count = 0
        return False

    # POSTメソッド用
    def post_request(self, endpoint, params=None, headers=None):
        url = self.BASE_URL.format(endpoint)
        while self.error_count < self.ERROR_LIMIT:
            try:
                response = self.session.post(url, data=params, headers=headers)
                if response.status_code != 200:
                    print(response)
                    self.error_count += 1
                    time.sleep(self.SLEEP)
                    continue
                self.error_count = 0
                return response
            except Exception as e:
                print(e)
                self.error_count += 1
                time.sleep(self.SLEEP)
                continue

        self.error_count = 0
        return False
