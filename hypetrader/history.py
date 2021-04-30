#!/usr/bin/env python
import requests
import json
import os
import pandas as pd

from utilities import *


BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}"


def fetch(symbol, epoch, interval="1m", limit=1):
    response = requests.request("GET", BINANCE_URL.format(symbol, interval, limit, epoch))
    result = json.loads(response.text)
    return result
    
def download_history_fast(symbol, start, freq=60, days=90):
    millis_in_period = days * 24 * 60 * 60 * 1000
    epoch = to_epoch(start)
    epoch_at_start = epoch
    interval = to_interval[freq]
    values = []

    completed = False
    while not completed:
        values_batch = fetch(symbol, epoch, interval=interval, limit=1000)
        for value in values_batch:
            obj = {"index": len(values), "epoch": value[0], "timestamp": to_readable(value[0]), "value": value[1]}
            values.append(obj)
            if value[0] >= epoch_at_start + millis_in_period:
                completed = True
                break
        print(f"Fetched {len(values)} values at {to_readable(epoch)}...")
        epoch = values[-1]["epoch"] + freq * 60000
    df = pd.DataFrame()
    df['ds'] = [datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S') for v in values]
    df['open'] = [get_value(v) for v in values]
    return df


if __name__ == '__main__':
	df = download_history_fast('BNBBUSD', '20210227235000', freq=5, days=60)
	print(df)
