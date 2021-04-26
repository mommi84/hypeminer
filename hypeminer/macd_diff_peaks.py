#!/usr/bin/env python
import os
import json
import pandas as pd
from datetime import datetime
from IPython.display import display
import requests


os.chdir('../misc/optimisation') 


symbol = 'BNBUSDT'
start = '20200101000000'
freq = 5
days = 365

strategy = 'MACDDAPnL'

# ---------------------------------------------------------

FEES = 0.001

def to_datetime(timestamp):
    return datetime(
      int(timestamp[0:4]), int(timestamp[4:6]), int(timestamp[6:8]), 
      int(timestamp[8:10]), int(timestamp[10:12]), int(timestamp[12:14])
  )

def get_value(v):
    try:
        return float(v['value'])
    except:
        return float(v['value'][0][1])

def load_file(file):
    df = pd.DataFrame()
    with open(file) as f:
        data = json.load(f)
    df['ds'] = [datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S') for v in data]
    df['open'] = [get_value(v) for v in data]
    return df

def display_whole(dframe):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        display(dframe)

strategies = {
    'MACDDPnL': "MACD Diff Peak&Limit",
    'MACDDAPnL': "MACD Diff Adaptive Peak&Limit",
    'MACDDPeaks': "MACD Diff Peaks",
    'MACDVigano': "MACD Viganò HistoCross"
}

run_id = f"{symbol}-{start}-{freq}-{days}-{strategy}"
run_title = f"{symbol} - {strategies[strategy]} at {days} days from " \
            f"{to_datetime(start).strftime('%Y-%m-%d')} every {freq} minutes"
file = f"{symbol}-{start}-{freq}-{days}.json"

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

def to_epoch(timestamp, milliseconds=True):
    dt = to_datetime(timestamp)
    epoch = dt.timestamp()
    if milliseconds:
        return int(epoch * 1000)
    else:
        return int(epoch)
    
def to_readable(epoch):
    return datetime.fromtimestamp(epoch/1000).strftime('%Y-%m-%d %H:%M:%S')

BINANCE_URL = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}"

def fetch(symbol, epoch, interval="1m", limit=1):
    response = requests.request("GET", BINANCE_URL.format(symbol, interval, limit, epoch))
    result = json.loads(response.text)
    return result
    
def download_history_fast(symbol, start, delta_minutes=60, days=90):
    millis_in_period = days * 24 * 60 * 60 * 1000
    file_dest = f"{symbol}-{start}-{delta_minutes}-{days}.json"
    if os.path.isfile(file_dest):
        return
    epoch = to_epoch(start)
    epoch_at_start = epoch
    interval = to_interval[delta_minutes]
    values = []
    i = 0
    completed = False
    while not completed:
        values_batch = fetch(symbol, epoch, interval=interval, limit=1000)
        for value in values_batch:
            obj = {"index": i, "timestamp": to_readable(value[0]), "value": value[1]}
            values.append(obj)
            i += 1
            if value[0] >= epoch_at_start + millis_in_period:
                completed = True
                break
        print(f"Fetched {len(values)} values at {to_readable(epoch)}...")
        epoch += 1000 * delta_minutes * 60000

    with open(file_dest, 'w') as f_out:
        json.dump(values, f_out)

download_history_fast(symbol, start, delta_minutes=freq, days=days)

df_orig = load_file(file)

# exponential moving average
def ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()

df_orig['ema12'] = ema(df_orig['open'], 12)
df_orig['ema26'] = ema(df_orig['open'], 26)
df_orig['macd'] = df_orig['ema12'] - df_orig['ema26']
df_orig['signal'] = ema(df_orig['macd'], 9)
df_orig['macddiff'] = df_orig['macd'] - df_orig['signal']

df_orig['prev_open'] = df_orig['open'].shift(1)
df_orig['is_negative'] = df_orig['macddiff'] < 0
df_orig['is_upward'] = df_orig['macddiff'].diff() > 0

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as colors
plt.style.use('ggplot')

def plot(typ, df_plot, cols, title=None, baseline=None, fig_file=None):
    plt.rcParams["figure.figsize"] = (20, 8)
    plt.clf()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    for col in cols:
        if typ == 'line':
            plt.plot(df_plot['ds'], df_plot[col], label=col)
        elif typ == 'bars':
            plt.bar(df_plot['ds'], df_plot[col], color='#009900', label=col, width=.005)
    if baseline:
        try:
            for bl in baseline:
                plt.axhline(y=bl, color='b', linestyle='-', label='baseline')
        except:
            plt.axhline(y=baseline, color='b', linestyle='-', label='baseline')
    plt.legend(loc="best", prop={'size': 12})
    if not title:
        title = f"{symbol} - freq={freq}"
    plt.title(title)
    plt.gcf().autofmt_xdate()
    if not fig_file:
        fig_file = f"plots/{strategy}/{run_id}.png"
    plt.savefig(fig_file)

def compute_macd_diff_peak_and_limit(df_macddpnl_orig, take_profit=None, take_profit_bias=0, stop_loss=None, verbose=False, plot_chart=False):

    df_macddpnl = df_macddpnl_orig.copy()

    if take_profit is not None: # static values
        df_macddpnl['take_profit'] = take_profit
    else:
        assert 'take_profit' in df_macddpnl

    if stop_loss is not None: # static values
        df_macddpnl['stop_loss'] = stop_loss
    else:
        assert 'stop_loss' in df_macddpnl

    df_macddpnl['suggest'] = 'IDLE'
    df_macddpnl.loc[df_macddpnl['is_negative'] & df_macddpnl['is_upward'] & (df_macddpnl['take_profit'] < np.inf), 'suggest'] = 'BUY'

    # with an adaptive take_profit, stop_loss might no longer be necessary, as take_profit will decrease with the price
    df_macddpnl['take_profit'] = df_macddpnl['take_profit'] + take_profit_bias

    df_macddpnl['limit_zeroes'] = 0
    df_macddpnl.loc[df_macddpnl['suggest'] == 'BUY', 'limit_zeroes'] = df_macddpnl['open'] * df_macddpnl['take_profit']

    limit_array = list(df_macddpnl['limit_zeroes'])
    for i, x in enumerate(limit_array):
        if i > 0 and x == 0:
            limit_array[i] = limit_array[i - 1]
    df_macddpnl['limit'] = limit_array
    del df_macddpnl['limit_zeroes']

    df_macddpnl['stop_zeroes'] = 0
    df_macddpnl.loc[df_macddpnl['suggest'] == 'BUY', 'stop_zeroes'] = df_macddpnl['open'] * df_macddpnl['stop_loss']

    stop_array = list(df_macddpnl['stop_zeroes'])
    for i, x in enumerate(stop_array):
        if i > 0 and x == 0:
            stop_array[i] = stop_array[i - 1]
    df_macddpnl['stop'] = stop_array
    del df_macddpnl['stop_zeroes']

    s = 'OUT' # IN=invested, OUT=liquidated
    action_values = []
    result_values = []

    assets = 1
    assets_values = []
 
    investment = None
    investment_values = []

    investment_when = None
    investment_when_values = []

    investment_open = None
    investment_open_values = []

    for index, row in df_macddpnl.iterrows():
        if s == 'IN': # this depends on the previous state
            assets = assets / row['prev_open'] * row['open']
        if s == 'OUT' and row['suggest'] == 'BUY':
            s = 'IN'
            action_values.append('BUY')
            result_values.append(np.nan)
            assets = assets * (1 - FEES)
            investment = assets
            investment_values.append(np.nan)
            investment_when = row['ds']
            investment_when_values.append(np.nan)
            investment_open = row['open']
            investment_open_values.append(investment_open)
        elif s == 'IN' and (row['open'] * (1-FEES) >= row['limit'] or row['open'] <= row['stop']):
            s = 'OUT'
            action_values.append('SELL')
            result_values.append('GAIN' if assets >= investment else 'LOSS')
            assets = assets * (1 - FEES)
            investment_values.append(investment)
            investment_when_values.append(investment_when)
            investment_open_values.append(investment_open)
        else:
            action_values.append('----')
            result_values.append(np.nan)
            investment_values.append(np.nan)
            investment_when_values.append(np.nan)
            investment_open_values.append(investment_open)
        assets_values.append(assets)

    df_macddpnl['assets'] = assets_values
    df_macddpnl['action'] = action_values
    df_macddpnl['result'] = result_values
    df_macddpnl['investment'] = investment_values
    df_macddpnl['invest_when'] = investment_when_values
    df_macddpnl['invest_open'] = investment_open_values

    comparable_from = df_macddpnl.index[df_macddpnl['take_profit'] < np.inf].to_list()[0]
    print(f"Comparable from: {df_macddpnl['ds'].iloc[comparable_from]}")
    bnh = df_macddpnl['open'].iloc[-1] / df_macddpnl['open'].iloc[comparable_from]
    
    if verbose:
        display(df_macddpnl[:30])
    
    if plot_chart:
        df_macddpnl['buy-and-hold'] = df_macddpnl['open'] / df_macddpnl['open'].iloc[comparable_from]
        plot_title = f"{symbol} - {strategies[strategy]} - take_profit={take_profit} take_profit_bias={take_profit_bias} stop_loss={stop_loss}" if take_profit and stop_loss else \
                     f"{symbol} - {strategies[strategy]} - freq={freq} take_profit_bias={take_profit_bias}"
        plot('line', df_macddpnl.iloc[comparable_from:], ['assets', 'buy-and-hold'], title=plot_title)
    
    return assets, bnh, df_macddpnl


import numpy as np
from joblib import Parallel, delayed
import multiprocessing




LIMIT_RANGE = [101, 111, 1]
STOP_LOSS_RANGE = [80, 99, 2]


class MidpointNormalize(colors.Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        colors.Normalize.__init__(self, vmin, vmax, clip)
    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y), np.isnan(value))

def build_heatmap(heat, file_id, xs, ys, fig_file=None):
    info = file_id.split('-')

    X, Y = np.meshgrid(xs, ys)
    Z = np.array(heat['stake']).reshape(X.shape)
    bnh = heat['baseline'].iloc[-1]

    # heatmap
    plt.rcParams["figure.figsize"] = (20, 12)
    plt.clf()
    plt.xticks(range(len(xs)), [f"+{(x-1)*100:.0f}%" for x in xs])
    plt.yticks(range(len(ys)), [f"-{(1-y)*100:.0f}%" for y in ys])
    plt.grid(False)
    plt.title(run_title)
    plt.xlabel('take_profit')
    plt.ylabel('stop_loss')
    heat = plt.imshow(Z, cmap='RdBu', norm=MidpointNormalize(midpoint=bnh))
    plt.colorbar(heat)
    if not os.path.exists(f"plots/{info[4]}"):
        os.makedirs(f"plots/{info[4]}")
    if not fig_file:
        fig_file = f"plots/{info[4]}/{file_id}.png"
    plt.savefig(fig_file)


def optimise(df_opt, run_id, tsv_file=None):
        
    if not tsv_file:
        tsv_file = f"{run_id}.tsv"
        print(f"started: {df_opt['ds'].iloc[0]}")
    
    # limit
    # xs = np.arange(101, 121, 1) / 100
    xs = np.arange(LIMIT_RANGE[0], LIMIT_RANGE[1]+1, LIMIT_RANGE[2]) / 100
    # stop_loss
    # ys = np.arange(80, 100, 1) / 100
    ys = np.arange(STOP_LOSS_RANGE[0], STOP_LOSS_RANGE[1]+1, STOP_LOSS_RANGE[2]) / 100

    if not os.path.isfile(tsv_file):
        heat = pd.DataFrame()
        take_profits, stop_losses, baselines, stakes = [], [], [], []
        for stop_loss in ys:
            for take_profit in xs:
                stake, baseline, _ = compute_macd_diff_peak_and_limit(df_opt, take_profit=take_profit, stop_loss=stop_loss)
                print("\t".join([run_id] + ["{:.2f}".format(x) for x in [take_profit, stop_loss, baseline, stake]]).expandtabs(8))
                take_profits.append(take_profit)
                stop_losses.append(stop_loss)
                baselines.append(baseline)
                stakes.append(stake)
        heat['target'] = take_profits
        heat['stop_loss'] = stop_losses
        heat['baseline'] = baselines
        heat['stake'] = stakes
        heat.to_csv(tsv_file, sep='\t', index=False)
    else:
        heat = pd.read_csv(tsv_file, sep='\t')
    
    return heat, xs, ys

OPT_WINDOW_DAYS = 60

def complete_optimisation():
    obj_list = []
    for t_days in range(0, 306):
        opt_start = int(60 / freq) * 24 * t_days
        opt_end = int(60 / freq) * 24 * (t_days + OPT_WINDOW_DAYS)
        df_test = df_orig.iloc[opt_start : opt_end]
        file_id = f"window-test/{start[:4]}_ow{OPT_WINDOW_DAYS}_t{t_days}"
        obj_list.append({'df': df_test, 'start': df_test['ds'].iloc[0], 'end': df_test['ds'].iloc[-1], 'id': file_id})

    results = Parallel(n_jobs=multiprocessing.cpu_count())(
        delayed(optimise)(
            df_opt=x['df'], run_id=run_id, tsv_file=f"{x['id']}.tsv"
        ) for x in obj_list)

    for x, (heat, xs, ys) in zip(obj_list, results):
        print(x)
        build_heatmap(heat, run_id, xs, ys, fig_file=f"{x['id']}.png")

# complete_optimisation()

df_sim = df_orig.copy()

just_dates, take_profits, stop_losses = [], [], []

df_best = pd.DataFrame()

for t_days in range(0, 306):
    file_id = f"window-test/{start[:4]}_ow{OPT_WINDOW_DAYS}_t{t_days}"
    opt_start = int(60 / freq) * 24 * t_days
    opt_end = int(60 / freq) * 24 * (t_days + OPT_WINDOW_DAYS)
    df_test = df_sim.iloc[opt_start : opt_end]
    date_start = df_test['ds'].iloc[0]
    date_end = df_test['ds'].iloc[-1]
    heat, _, _ = optimise(None, run_id, tsv_file=f"{file_id}.tsv")
    best_take_profit, best_stop_loss, _, _, = heat.sort_values(by='stake', ascending=False).iloc[0]
    date_now = df_sim['ds'].iloc[opt_end].date()
    just_dates.append(date_now)
    take_profits.append(best_take_profit)
    stop_losses.append(best_stop_loss)

df_best['x'] = just_dates
df_best['just_date'] = df_best['x'].astype('datetime64[ns]')
del df_best['x']
df_best['take_profit'] = take_profits
df_best['stop_loss'] = stop_losses

df_sim['just_date'] = df_sim['ds'].dt.date.astype('datetime64[ns]')

df_sim = df_sim.join(df_best.set_index('just_date'), on='just_date', lsuffix='_caller', rsuffix='_other')

df_sim['take_profit'] = df_sim['take_profit'].replace(np.nan, np.inf)
df_sim['stop_loss'] = df_sim['stop_loss'].replace(np.nan, 0)

print(df_sim)

bias = 0.007 # additional +0.7%
stop_loss = 0

assets, bnh, df_sim = compute_macd_diff_peak_and_limit(df_sim, take_profit_bias=bias, stop_loss=stop_loss, verbose=False, plot_chart=True)

print(df_sim[df_sim['action'] == 'SELL'])

print(f"assets: {assets}, buy-and-hold: {bnh}")

slc = int(len(df_sim) / 48)

plot('line', df_sim.iloc[9*slc:10*slc], ['assets', 'buy-and-hold'], 
    title=f"{symbol} - {strategies[strategy]} - freq={freq} take_profit_bias={bias}", 
    fig_file=f"plots/{strategy}/{run_id}_zoom.png")

df_sim.iloc[18526:19657].to_csv(f"plots/{strategy}/{run_id}_analysis.tsv", sep='\t')
