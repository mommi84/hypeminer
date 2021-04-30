#!/usr/bin/env python
import numpy as np
from datetime import datetime, timedelta

from hypetrader.utilities import *
from hypetrader.history import download_history_fast


def do_nothing(state):
    pass


class State(object):
    def __getattr__(self, name):
        return None


def _do_calculations(df):

    df['ema12'] = ema(df['open'], 12)
    df['ema26'] = ema(df['open'], 26)
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = ema(df['macd'], 9)
    df['macddiff'] = df['macd'] - df['signal']

    df['prev_open'] = df['open'].shift(1)
    df['is_negative'] = df['macddiff'] < 0
    df['is_upward'] = df['macddiff'].diff() > 0

    return df


def compute_macd_diff_peak_and_limit(state, simulate=True):

    take_profit = state.take_profit
    stop_loss = state.stop_loss
    df_stg = state.df_stg
    take_profit_bias = 0 if state.take_profit_bias is None else state.take_profit_bias

    df = _do_calculations(df_stg)

    if take_profit is not None: # static values
        df['take_profit'] = take_profit
    else:
        assert 'take_profit' in df

    if stop_loss is not None: # static values
        df['stop_loss'] = stop_loss
    else:
        assert 'stop_loss' in df

    df['suggest'] = 'IDLE'
    df.loc[df['is_negative'] & df['is_upward'] & (df['take_profit'] < np.inf), 'suggest'] = 'BUY'

    # with an adaptive take_profit, stop_loss might no longer be necessary, as take_profit will decrease with the price
    df['take_profit'] = df['take_profit'] + take_profit_bias

    df['limit_zeroes'] = 0
    df.loc[df['suggest'] == 'BUY', 'limit_zeroes'] = df['open'] * df['take_profit']

    limit_array = list(df['limit_zeroes'])
    for i, x in enumerate(limit_array):
        if i > 0 and x == 0:
            limit_array[i] = limit_array[i - 1]
    df['limit'] = limit_array
    del df['limit_zeroes']

    df['stop_zeroes'] = 0
    df.loc[df['suggest'] == 'BUY', 'stop_zeroes'] = df['open'] * df['stop_loss']

    stop_array = list(df['stop_zeroes'])
    for i, x in enumerate(stop_array):
        if i > 0 and x == 0:
            stop_array[i] = stop_array[i - 1]
    df['stop'] = stop_array
    del df['stop_zeroes']

    if not simulate:
        return

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

    sell_count = {'at_profit': 0, 'at_loss': 0}

    for index, row in df.iterrows():
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
            if row['open'] * (1-FEES) >= row['limit']:
                sell_count['at_profit'] += 1
            else:
                sell_count['at_loss'] += 1
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

    df['assets'] = assets_values
    df['action'] = action_values
    df['result'] = result_values
    df['investment'] = investment_values
    df['invest_when'] = investment_when_values
    df['invest_open'] = investment_open_values

    df['decision'] = '----' # for the trader

    comparable_from = df.index[df['take_profit'] < np.inf].to_list()[0]
    # print(f"Comparable from: {df['ds'].iloc[comparable_from]}")
    bnh = df['open'].iloc[-1] / df['open'].iloc[comparable_from]

    state.stake = assets
    state.baseline = bnh
    state.sell_count = sell_count
    state.df_stg = df


def _optimise(state, df_opt, run_id):

    print(f"started optimisation: {run_id}")
    tsv_file = f"data/optimisation/{run_id}.tsv"
    png_file = f"data/optimisation/{run_id}.png"
    
    # limit
    xs = np.arange(LIMIT_RANGE[0], LIMIT_RANGE[1]+1, LIMIT_RANGE[2]) / 100
    # stop_loss
    ys = np.arange(STOP_LOSS_RANGE[0], STOP_LOSS_RANGE[1]+1, STOP_LOSS_RANGE[2]) / 100

    heat = pd.DataFrame()
    take_profits, stop_losses, baselines, stakes = [], [], [], []
    for stop_loss in ys:
        for take_profit in xs:
            state.take_profit, state.stop_loss, state.df_stg = take_profit, stop_loss, df_opt
            compute_macd_diff_peak_and_limit(state)
            stake, baseline, sell_count = state.stake, state.baseline, state.sell_count
            print("\t".join([f"{x:.2f}" for x in [take_profit, stop_loss]] + [f"{x:.3f}" for x in [baseline, stake]] + [f"{sell_count}"]).expandtabs(8))
            take_profits.append(take_profit)
            stop_losses.append(stop_loss)
            baselines.append(baseline)
            stakes.append(stake)
    heat['target'] = take_profits
    heat['stop_loss'] = stop_losses
    heat['baseline'] = baselines
    heat['stake'] = stakes
    heat.to_csv(tsv_file, sep='\t', index=False)
    
    return heat, xs, ys


def optimise_parameters(state):

    freq = state.freq
    symbol = state.symbol

    # initialise data: get current date and last x number of days before current (TODO caching)
    past_start_time = (datetime.utcnow() - timedelta(days=OPT_WINDOW_DAYS) - timedelta(minutes=freq)).strftime('%Y%m%d%H%M%S')
    df_opt = download_history_fast(symbol, past_start_time, freq=freq, days=OPT_WINDOW_DAYS)
    print(df_opt)

    # call optimisation
    date_start = to_safe(df_opt['ds'].iloc[0])
    date_end = to_safe(df_opt['ds'].iloc[-1])
    run_id = f"{symbol}-{date_start}-{date_end}"
    heat, _, _ = _optimise(state, df_opt, run_id)

    state.best_take_profit, state.best_stop_loss, _, _, = heat.sort_values(by='stake', ascending=False).iloc[0]
    print(f"best_take_profit: {state.best_take_profit}, best_stop_loss: {state.best_stop_loss}")

    state.df_stg = state.df_stg.iloc[:-1].copy()


def call_macddpnl(state):
    state.take_profit = state.best_take_profit
    state.take_profit_bias = TAKE_PROFIT_BIAS # additional +0.7%
    state.stop_loss = 0

    compute_macd_diff_peak_and_limit(state, simulate=False)

    suggest = state.df_stg['suggest'].iloc[-1]
    prev_suggest = state.df_stg['suggest'].iloc[-2]
    open_price = state.df_stg['open'].iloc[-1]
    limit = state.df_stg['limit'].iloc[-1]

    if not state.invested and suggest == 'BUY' and prev_suggest == 'IDLE':
        state.invested = True
        return 'BUY'

    if state.invested and open_price * (1 - FEES) > limit:
        state.invested = False
        return 'SELL'

    return 'IDLE'


STRATEGY_PLANNING = {
    'MACDDiffAdaptivePeakAndLimit': {
        'daily': do_nothing,
        'hourly': optimise_parameters,
        'periodically': call_macddpnl,
    }
}
