#!/usr/bin/env python
from binance.client import Client
import configparser


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


    def get_exchange_info(self):
        return self.client.get_exchange_info()

    
    def get_step_size(self):
        for f in self.client.get_symbol_info(self.symbol)['filters']:
            if f['filterType'] == 'LOT_SIZE':
                return float(f['stepSize'])
