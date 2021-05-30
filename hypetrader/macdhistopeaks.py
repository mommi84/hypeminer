#!/usr/bin/env python
from datetime import datetime, timedelta
from itertools import product

from hypetrader.history import download_history_fast
from hypetrader.utilities import *


def _apply_fees(x):
    return x * (1 - FEES)


def _ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()


def _technical_analysis(df, freq):
    df['change_norm_1'] = 100.0 * df['close'].diff() / df['close'].shift(1)

    df['ma50'] = df['close'].rolling(window=50).mean()

    df['ema12'] = _ema(df['close'], 12)
    df['ema26'] = _ema(df['close'], 26)
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = _ema(df['macd'], 9)
    df['macd_histo'] = df['macd'] - df['signal']

    df['macd_histo_norm'] = 50000.0 * df['macd_histo'] / df['ma50'] * (freq ** (-1/2))    # ideally in [-100, +100]

    return df


def _simulate(df, macd_thr):
    df['action'] = None
    df['prev_close'] = df['close'].shift(1)
    df['stake'] = None
    df['profits'] = None
    df['last_buy'] = None
    df['last_sell'] = None

    invested = False
    last_buy = 1
    last_sell_close = 0
    last_sell_elapsed = last_buy_elapsed = 0
    profits, last_buys, last_sells = [], [], []
    stakes = []
    actions = []
    stake = 1

    # important: only access constant values with row[]
    for i, (index, row) in enumerate(df.iterrows()):
        # stake accrued
        if invested:
            stake = stake / row['prev_close'] * row['close']
        profit_if_sell = _apply_fees(stake) - last_buy
        profit_rate_if_buy = last_sell_close - row['close'] - row['close'] * FEES
        # follow action
        if _buy_signal(row['macd_histo_norm'], macd_thr) and not invested:
            action = 'BUY'
            stake = _apply_fees(stake)
            invested = True
            profits.append(None)
            last_buy = stake
            last_buys.append(last_buy)
            last_sells.append(0)
            last_sell_elapsed += 1
            last_buy_elapsed = 0
        elif _sell_signal(row['macd_histo_norm'], macd_thr) and invested:
            action = 'SELL'
            stake = _apply_fees(stake)
            invested = False
            profits.append(profit_if_sell)
            last_sell_close = row['close']
            last_sells.append(last_sell_close)
            last_buys.append(0)
            last_sell_elapsed = 0
            last_buy_elapsed += 1
        else:
            action = '----'
            profits.append(None)
            last_buys.append(0)
            last_sells.append(0)
            last_sell_elapsed += 1
            last_buy_elapsed += 1
        stakes.append(stake)
        actions.append(action)
    
    df['stake'] = stakes
    df['action'] = actions
    df['profits'] = profits
    df['last_buy'] = last_buys
    df['last_sell'] = last_sells
    del df['prev_close']
        
    close0 = df['close'].iloc[0]
    df['hold'] = df['close'] / close0
    final_stake = df['stake'].iloc[-1]
    final_hold = df['hold'].iloc[-1]
    
    stats = {'stake_hold_rate': round(final_stake / final_hold, 3), 
             'stake': round(final_stake, 3), 'hold': round(final_hold, 3), 
             'profit_count': len(df[df['profits'] > 0]), 'loss_count': len(df[df['profits'] < 0])}
    
    return df, stats


def _get_now_minus_days(freq, days):
    return (datetime.utcnow() - timedelta(days=days) - 2 * timedelta(minutes=freq)).strftime('%Y%m%d%H%M%S')


def _trace(string, verbose=True):
    if verbose:
        print(string)


def _single_run(symbol, start, freq, days, macd_thr, verbose=True):
    df = download_history_fast(symbol, start, freq=freq, days=days, init_index=True)
    _technical_analysis(df, freq)
    df.dropna(inplace=True)
    _trace(f"MACD thr: {macd_thr}", verbose=verbose)
    df, stats = _simulate(df, macd_thr)
    _trace(stats, verbose=verbose)
    return df, stats


def optimise(state, simulation_days=1):

    if state.invested:
        print("Optimisation skipped.")
        return None, None

    print("Starting optimisation...")
    simulation_start = _get_now_minus_days(freq=state.freq, days=simulation_days)
    opt = {}
    for a, b in product(range(0, 100 + 1, 10), range(0, 100 + 1, 10)):
        _, stats = _single_run(symbol=state.symbol, start=simulation_start, freq=state.freq, days=simulation_days, macd_thr=[-a, b], 
                          verbose=False)
        opt[(-a,b)] = stats['stake_hold_rate']
    ranking = dict(sorted(opt.items(), key=lambda item: item[1], reverse=True)).items()
    for i, (k, v) in zip(range(10), ranking):
        print(f"{v:.3f} {k}")
    best_a, best_b = list(ranking)[0][0]
    print(f"\nbest: {(best_a, best_b)}\n")

    # update parameters
    state.macd_thr = [best_a, best_b]
    # state.df_stg.loc[state.df_stg.index[-1], 'macd_thr_a'] = best_a
    # state.df_stg.loc[state.df_stg.index[-1], 'macd_thr_b'] = best_b

    return best_a, best_b


def initialise(state):

    # initialise data: get current date and last day (TODO caching)
    past_start_time = (datetime.utcnow() - timedelta(days=1) - 2 * timedelta(minutes=state.freq)).strftime('%Y%m%d%H%M%S')
    df = download_history_fast(state.symbol, past_start_time, freq=state.freq, days=1)

    # remove last row as it is added periodically
    state.df_stg = df.iloc[:-1].copy()

    state.df_stg['macd_thr_a'] = None
    state.df_stg['macd_thr_b'] = None

    _ = optimise(state)


def _buy_signal(macd_histo_norm, macd_thr):
    return macd_histo_norm <= macd_thr[0]


def _sell_signal(macd_histo_norm, macd_thr):
    return macd_histo_norm >= macd_thr[1]


def act(state):

    state.df_stg = _technical_analysis(state.df_stg, state.freq)

    macd_histo_norm = state.df_stg['macd_histo_norm'].iloc[-1]

    if not state.invested and _buy_signal(macd_histo_norm, state.macd_thr):
        state.invested = True
        return 'BUY'

    if state.invested and _sell_signal(macd_histo_norm, state.macd_thr):
        state.invested = False
        return 'SELL'

    return 'IDLE'
