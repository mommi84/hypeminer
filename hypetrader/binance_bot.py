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
        return self.client.get_all_orders(symbol=self.symbol)


    def free_balance(self, asset, fees=False):
        balance = float(self.client.get_asset_balance(asset=asset)['free'])
        if not fees:
            return balance
        else:
            return (1 - FEES) * balance


    def get_ticker_price(self):
        return float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])


    def get_complete_candle(self, freq):
        candles = self.client.get_klines(symbol=self.symbol, interval=to_interval[freq], limit=2)
        value = candles[0]
        return {"epoch": value[0], "timestamp": to_readable_utc(value[0]), "open": float(value[1]), 
                   "high": float(value[2]), "low": float(value[3]), "close": float(value[4]), 
                   "volume": float(value[5]), "trades": value[8]}


    def buy(self, at_price, perc=100):

        available_balance = self.free_balance(self.fiat, fees=True)
        print(f"{self.fiat} available: {available_balance}")

        balance_to_invest = available_balance * perc / 100
        print(f"{self.fiat} to trade: {balance_to_invest}")

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
        print(f"{self.crypto} to trade: {balance_to_sell}")

        print(f"{self.crypto} price in {self.fiat}: {at_price}")

        precision = int(round(- math.log(self.step_size, 10), 0))
        qty = round(balance_to_sell * (1 - FEES), precision)
        print(f"{self.crypto} to sell: {qty}")

        order = self.client.order_market_sell(
            symbol=self.symbol,
            quantity=qty
        )

        return order

    def sell_stop_limit(self, stop, limit, perc=100):

        if self.fiat == 'BUSD':
            stop = round(stop, 1)
            limit = round(limit, 1)
        else:
            print(f"Please check decimals for {self.fiat}.")

        available_balance = self.free_balance(self.crypto, fees=True)
        print(f"{self.crypto} available: {available_balance}")

        balance_to_sell = available_balance * perc / 100
        print(f"{self.crypto} to trade: {balance_to_sell}")

        precision = int(round(- math.log(self.step_size, 10), 0))
        qty = math.floor(balance_to_sell * 10 ** precision) / 10 ** precision
        print(f"{self.crypto} to sell: {qty}")

        order = self.client.order_oco_sell(
            symbol=self.symbol,
            quantity=qty,
            price=limit,
            stopPrice=stop,
            stopLimitPrice=stop,
            stopLimitTimeInForce='GTC'
        )

        return order



if __name__ == '__main__':
    bot = BinanceBot('BNB', 'BUSD')
    price = bot.get_ticker_price()
    print(f"{bot.crypto} price in {bot.fiat}: {price}")

    balance = bot.free_balance(bot.fiat, fees=True)
    print(f"Available {bot.fiat}: {balance}")

    # buy_order = bot.buy(price, perc=1)
    # print(buy_order)

    # sell_order = bot.sell_stop_limit(price * 0.97, price * 1.02, perc=100)
    # print(sell_order)
