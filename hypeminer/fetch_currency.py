#!/usr/bin/env python
import requests
import json


BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval=1m&limit=1"


class CurrencyFetcher(object):

	"""CurrencyFetcher object."""
	def __init__(self):
		pass
		
	def fetch_value(self, currency):
		response = requests.request("GET", BINANCE_URL.format(currency))
		result = json.loads(response.text)
		return {'currency': currency, 'timestamp': result[0][0], 'value': result[0][1]}

if __name__ == '__main__':
	f = CurrencyFetcher()
	result = f.fetch_value("BTCUSDT")
	print(result)
