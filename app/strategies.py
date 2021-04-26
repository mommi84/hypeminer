#!/usr/bin/env python
import numpy as np


def compute_macd_diff_peak_and_limit(df_orig, take_profit=None, take_profit_bias=0, stop_loss=None):

    df = df_orig.copy()

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

    comparable_from = df.index[df['take_profit'] < np.inf].to_list()[0]
    print(f"Comparable from: {df['ds'].iloc[comparable_from]}")
    bnh = df['open'].iloc[-1] / df['open'].iloc[comparable_from]

    return assets, bnh, df

