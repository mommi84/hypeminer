#!/usr/bin/env python
from binance.client import Client
import configparser
import math

from app.utilities import *


class BinanceInterface(object):

    """docstring for BinanceInterface"""
    def __init__(self, crypto, fiat):
        self.crypto = crypto
        self.fiat = fiat
        self.symbol = f"{crypto}{fiat}"
        self.configure()
        self.step_size = self.get_step_size()


    def configure(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        api_key = config.get('Binance', 'api_key')
        api_secret = config.get('Binance', 'api_secret')
        self.client = Client(api_key, api_secret)

        
    def get_step_size(self):
        for f in self.client.get_symbol_info(self.symbol)['filters']:
            if f['filterType'] == 'LOT_SIZE':
                return float(f['stepSize'])


    def get_all_orders(self):
        return self.client.get_all_orders(symbol=self.symbol)


    def free_balance(self, asset, fees=False):
        balance = float(self.client.get_asset_balance(asset=asset)['free'])
        if not fees:
            return balance
        else:
            return (1 - FEES) * balance


    def get_ticker_price(self):
        return float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])


    def buy_all_in(self, at_price):

        available_balance = self.free_balance(self.fiat, fees=True)

        print(f"Available {self.fiat}: {available_balance}")

        precision = int(round(- math.log(self.step_size, 10), 0))

        print(f"{self.crypto} price in {self.fiat}: {at_price}")

        qty = round(available_balance / at_price, precision)

        print(f"{self.crypto} to buy: {qty}")

        order = self.client.order_market_buy(
            symbol=self.symbol,
            quantity=qty
        )

        return order

    def get_ticket_price(self):
        return self.client.get_symbol_ticker(symbol=f"{self.crypto}{self.fiat}")['price']