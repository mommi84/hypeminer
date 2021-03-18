#!/usr/bin/env python
import requests
import json
from datetime import datetime


BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval=1m&limit=1&startTime={}"


class CurrencyFetcher(object):

	"""CurrencyFetcher object."""
	def __init__(self):
		pass
	
	def fetch_value(self, currency, timestamp):
		y = int(timestamp[0:4])
		mo = int(timestamp[4:6])
		d = int(timestamp[6:8])
		h = int(timestamp[8:10])
		mi = int(timestamp[10:12])
		s = int(timestamp[12:14])
		epoch = str(int(datetime(y, mo, d, h, mi, s).timestamp() * 1000))
		response = requests.request("GET", BINANCE_URL.format(currency, epoch))
		result = json.loads(response.text)
		return {'currency': currency, 'timestamp': result[0][0], 'value': result[0][1]}

if __name__ == '__main__':
	f = CurrencyFetcher()
	result = f.fetch_value("BTCUSDT", "20210318021353")
	print(result)
