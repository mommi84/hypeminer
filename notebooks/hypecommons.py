#!/usr/bin/env python
import os
import json
import pandas as pd
from datetime import datetime
from IPython.display import display
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from math import ceil
from tqdm import trange, tqdm


FEES = 0.0012
BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}"
to_interval = { 1: '1m', 3: '3m', 5: '5m', 15: '15m', 30: '30m', 60: '1h', 120: '2h', 240: '4h', 360: '6h', 480: '8h', 720: '12h', 1440: '1d', 4320: '3d', 10080: '1w' }

plt.style.use('ggplot')


def init_experiment(osys='Windows'):
    if osys == 'Windows':
        os.chdir('C:/Users/Agando/Workspace/hypeminer/misc/optimisation')
    elif osys == 'Linux':
        os.chdir('/home/tom/Workspace/hypeminer/misc/optimisation')
    else:
        raise Exception

def to_datetime(timestamp):
    return datetime(
      int(timestamp[0:4]), int(timestamp[4:6]), int(timestamp[6:8]), 
      int(timestamp[8:10]), int(timestamp[10:12]), int(timestamp[12:14])
  )

def load_file(file):
    with open(file) as f:
        data = json.load(f)
    index = [datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S') for v in data]
    df = pd.DataFrame(index=index)
    for field in ['open', 'high', 'low', 'close', 'volume', 'trades']:
        df[field] = [v[field] for v in data]
    return df

def display_whole(dframe):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        display(dframe)

def to_epoch(timestamp, milliseconds=True):
    dt = to_datetime(timestamp)
    epoch = dt.timestamp()
    if milliseconds:
        return int(epoch * 1000)
    else:
        return int(epoch)
    
def to_readable(epoch):
    return datetime.fromtimestamp(epoch/1000).strftime('%Y-%m-%d %H:%M:%S')

def plot(plt_fun, df_plot, cols, colours=None, linestyles=None, title=None, bar_size=None, baseline=None, baseline_names=None, is_date=True,
        fig_size=(20, 8), clf=True, show=True):
    plt.rcParams["figure.figsize"] = fig_size
    if clf:
        plt.clf()
    if is_date:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    if not colours:
        colours = len(cols) * [None]
    if not linestyles:
        linestyles = len(cols) * [None]
    for col, clr, lst in zip(cols, colours, linestyles):
        if bar_size:
            plt_fun(df_plot.index, df_plot[col], color=clr, label=col, width=bar_size)
        else:
            plt_fun(df_plot.index, df_plot[col], color=clr, label=col, linestyle=lst, drawstyle='steps-pre')
    if baseline:
        try:
            for bl, bln in zip(baseline, baseline_names):
                plt.axhline(y=bl, color='b', linestyle='--', label=bln)
        except:
            plt.axhline(y=baseline, color='b', linestyle='--', label='baseline')
    plt.legend(loc="best", prop={'size': 12})
    if not title:
        title = f""
    plt.title(title)
    plt.gcf().autofmt_xdate()
    
def output_chart(df, symbol, freq, save=False, fig_size=(20, 8), show=True, start_data=None):
    df_plot = df.copy()
    
    pts = int(len(df_plot)/3000) if len(df_plot) > 3000 else 1

    sells = df_plot[df_plot['action'] == 'SELL']
    buys = df_plot[df_plot['action'] == 'BUY']
    
    plot(plt.plot, df.iloc[::pts, :], ['close'], ['#888888'], title=f"{symbol} - freq={freq}", fig_size=fig_size, show=show)
    plt.scatter(sells.index, sells['close'], c='r', marker='v', s=120, label='sell')
    plt.scatter(buys.index, buys['close'], c='b', marker='^', s=120, label='buy')
    if start_data:
        if start_data[0] >= df_plot.index[0]:
            plt.scatter([start_data[0]], [start_data[1]], c='g', marker='*', s=150, label='trader start')
    plt.legend(loc="best", prop={'size': 12})
    if show:
        plt.show()
    if save:
        plt.savefig(save)

def fetch(symbol, epoch, interval="1m", limit=1):
    url = BINANCE_URL.format(symbol, interval, limit, epoch)
    response = requests.request("GET", url)
    result = json.loads(response.text)
    return result
    
def download_history_fast(symbol, start, freq=60, days=90):
    millis_in_period = days * 24 * 60 * 60 * 1000
    file_dest = f"{symbol}-{start}-{freq}-{days}.json"
    if os.path.isfile(file_dest):
#         print(f"File {file_dest} found.")
        return load_file(file_dest)
    epoch = to_epoch(start)
    epoch_at_start = epoch
    interval = to_interval[freq]
    values = []
    completed = False
    iters = ceil(millis_in_period / (freq * 60000) / 1000)
    for i in trange(iters, desc=f"Downloading {symbol} history", ncols=100):
        values_batch = fetch(symbol, epoch, interval=interval, limit=1000)
        for value in values_batch:
            obj = {"index": len(values), "epoch": value[0], "timestamp": to_readable(value[0]), "open": float(value[1]), 
                   "high": float(value[2]), "low": float(value[3]), "close": float(value[4]), "volume": float(value[5]), 
                   "trades": value[8]}
            values.append(obj)
            if value[0] >= epoch_at_start + millis_in_period:
                completed = True
                break
        epoch = values[-1]["epoch"] + freq * 60000
    with open(file_dest, 'w') as f_out:
        json.dump(values, f_out)
    
    return load_file(file_dest)
