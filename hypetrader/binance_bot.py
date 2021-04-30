#!/usr/bin/env python
from binance.client import Client
import configparser
import math

from hypetrader.utilities import *


class BinanceBot(object):

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
        return client.get_all_orders(symbol=self.symbol)


    def free_balance(self, asset, fees=False):
        balance = float(self.client.get_asset_balance(asset=asset)['free'])
        if not fees:
            return balance
        else:
            return (1 - FEES) * balance


    def get_ticker_price(self):
        return float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])


    def get_candle(self, freq):
        candles = self.client.get_klines(symbol=self.symbol, interval=to_interval[freq], limit=1)
        return candles[0][0], float(candles[0][1])


    def buy(self, at_price, perc=100):

        available_balance = self.free_balance(self.fiat, fees=True)
        print(f"{self.fiat} available: {available_balance}")

        balance_to_invest = available_balance * perc / 100
        print(f"{self.fiat} to invest: {balance_to_invest}")

        print(f"{self.crypto} price in {self.fiat}: {at_price}")

        precision = int(round(- math.log(self.step_size, 10), 0))
        qty = round(balance_to_invest / at_price, precision)
        print(f"{self.crypto} to buy: {qty}")

        order = self.client.order_market_buy(
            symbol=self.symbol,
            quantity=qty
        )

        return order


    def sell(self, at_price, perc=100):

        available_balance = self.free_balance(self.crypto, fees=True)
        print(f"{self.crypto} available: {available_balance}")

        balance_to_sell = available_balance * perc / 100
        print(f"{self.crypto} to sell: {balance_to_sell}")

        print(f"{self.crypto} price in {self.fiat}: {at_price}")

        precision = int(round(- math.log(self.step_size, 10), 0))
        qty = round(balance_to_sell / at_price, precision)
        print(f"{self.crypto} to sell: {qty}")

        order = self.client.order_market_sell(
            symbol=self.symbol,
            quantity=qty
        )

        return order


if __name__ == '__main__':
    bot = BinanceBot('VET', 'BUSD')
    # price = bot.get_ticker_price()
    # print(f"{bot.crypto} price in {bot.fiat}: {price}")
    balance = bot.free_balance(bot.fiat, fees=True)
    print(f"Available {bot.fiat}: {balance}")
