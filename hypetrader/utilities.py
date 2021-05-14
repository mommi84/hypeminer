#!/usr/bin/env python
import pandas as pd
from datetime import datetime
import pytz


# values to change more often
FEES = 0.0012
OPT_WINDOW_DAYS = 14
TAKE_PROFIT_BIAS = 0 # (additional +0.7% works well with BNBBUSD)

# values to change less often
LIMIT_RANGE = [101, 105, 1]
STOP_LOSS_RANGE = [90, 99, 2]
BINANCE_UPDATE_ALLOWANCE_SECONDS = 5

# universal constants
MINUTES_IN_A_DAY = 24 * 60
MINUTES_IN_AN_HOUR = 60


to_interval = {
    1: '1m',
    3: '3m',
    5: '5m',
    15: '15m',
    30: '30m',
    60: '1h',
    120: '2h',
    240: '4h',
    360: '6h',
    480: '8h',
    720: '12h',
    1440: '1d',
    4320: '3d',
    10080: '1w',
}


def to_epoch_utc(timestamp, milliseconds=True):
    dt = to_datetime(timestamp)
    epoch = dt.replace(tzinfo=pytz.utc).timestamp()
    if milliseconds:
        return int(epoch * 1000)
    else:
        return int(epoch)


def get_value(v):
    try:
        return float(v['open'])
    except:
        return float(v['open'][0][1])


def json_to_df(obj):
    d = {k: [] for k in obj[0]}
    for o in obj:
        for k, v in o.items():
            d[k].append(v)
    return pd.DataFrame.from_dict(d)


def to_readable_utc(epoch, millis=True):
    epoch = epoch / 1000 if millis else epoch
    return datetime.fromtimestamp(epoch).replace(tzinfo=pytz.utc).strftime('%Y-%m-%d %H:%M:%S')


def to_safe(timestamp):
	dt = datetime.strptime(str(timestamp), '%Y-%m-%d %H:%M:%S')
	return dt.strftime('%Y%m%d%H%M%S')

def to_datetime(timestamp):
    return datetime(
      int(timestamp[0:4]), int(timestamp[4:6]), int(timestamp[6:8]), 
      int(timestamp[8:10]), int(timestamp[10:12]), int(timestamp[12:14])
  	)

# exponential moving average
def ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()

def to_safe_string(epoch, millis=True):
    epoch = epoch / 1000 if millis else epoch
    return datetime.fromtimestamp(epoch).strftime('%Y%m%d%H%M%S')

def to_datetime_utc(epoch):
	return datetime.fromtimestamp(epoch / 1000, pytz.utc).replace(tzinfo=None)
