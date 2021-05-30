#!/usr/bin/env python
import requests
import json
import os
import pandas as pd

from hypetrader.utilities import *


BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}"


def fetch(symbol, epoch, interval="1m", limit=1):
    response = requests.request("GET", BINANCE_URL.format(symbol, interval, limit, epoch))
    result = json.loads(response.text)
    return result

def load_file(file, init_index=False):
    with open(file) as f:
        data = json.load(f)
    if init_index:
        index = [to_datetime_utc(v['epoch']) for v in data]
        df = pd.DataFrame(index=index)
    else:
        df = pd.DataFrame()
        df['ds'] = [to_datetime_utc(v['epoch']) for v in data]
    for field in ['open', 'high', 'low', 'close', 'volume', 'trades']:
        df[field] = [v[field] for v in data]
    return df
    
def download_history_fast(symbol, start, freq=60, days=90, init_index=False):
    file_dest = f"data/optimisation/{symbol}-{start}-{freq}-{days}.json"
    if os.path.isfile(file_dest):
        return load_file(file_dest)
    millis_in_period = days * 24 * 60 * 60 * 1000
    epoch = to_epoch_utc(start)
    epoch_at_start = epoch
    interval = to_interval[freq]
    values = []

    completed = False
    while not completed:
        values_batch = fetch(symbol, epoch, interval=interval, limit=1000)
        for value in values_batch:
            # obj = {"index": len(values), "epoch": value[0], "timestamp": to_readable_utc(value[0]), "value": value[1]}
            obj = {"index": len(values), "epoch": value[0], "timestamp": to_readable_utc(value[0]), "open": float(value[1]), 
                   "high": float(value[2]), "low": float(value[3]), "close": float(value[4]), "volume": float(value[5]), 
                   "trades": value[8]}
            values.append(obj)
            if value[0] >= epoch_at_start + millis_in_period:
                completed = True
                break
        print(f"Fetched {len(values)} values at {to_readable_utc(epoch)}...")
        epoch = values[-1]["epoch"] + freq * 60000
    with open(file_dest, 'w') as f_out:
        json.dump(values, f_out)
    
    return load_file(file_dest, init_index=init_index)


if __name__ == '__main__':
	df = download_history_fast('BNBBUSD', '20210227235000', freq=5, days=60)
	print(df)
