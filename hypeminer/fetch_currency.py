#!/usr/bin/env python
import requests
import json
import os

from hypeminer import utilities


BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval=1m&limit=1&startTime={}"


class CurrencyFetcher(object):

    """CurrencyFetcher object."""
    def __init__(self, currency):
        self.currency = currency

        self.cachefile = f"data/{self.currency}/cache.json"
        if os.path.isfile(self.cachefile):
            with open(self.cachefile) as f:
                self.cache = json.load(f)
        else:
            self.cache = {}
    
    def fetch_value(self, timestamp):
        epoch = utilities.to_epoch(timestamp, milliseconds=True)

        if timestamp in self.cache:
            return {'currency': self.currency, 'timestamp': epoch, 'value': self.cache[timestamp]}

        response = requests.request("GET", BINANCE_URL.format(self.currency, epoch))
        result = json.loads(response.text)

        self.cache[timestamp] = result[0][1]
        utilities.mkdir(f"data/{self.currency}/")
        with open(self.cachefile, 'w') as f_out:
            json.dump(self.cache, f_out)

        return {'currency': self.currency, 'timestamp': result[0][0], 'value': result[0][1]}

if __name__ == '__main__':
    f = CurrencyFetcher("BTCBUSD")
    result = f.fetch_value("20210318172600")
    print(result)
