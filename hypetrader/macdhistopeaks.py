#!/usr/bin/env python
from hypetrader.history import download_history_fast
from datetime import datetime, timedelta


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


def initialise(state):

    # initialise data: get current date and last day (TODO caching)
    past_start_time = (datetime.utcnow() - timedelta(days=1) - 2 * timedelta(minutes=state.freq)).strftime('%Y%m%d%H%M%S')
    df = download_history_fast(state.symbol, past_start_time, freq=state.freq, days=1)

    # remove last row as it is added periodically
    state.df_stg = df.iloc[:-1].copy()


def _buy_signal(macd_histo_norm, macd_thr):
    return macd_histo_norm <= macd_thr[0]


def _sell_signal(macd_histo_norm, macd_thr):
    return macd_histo_norm >= macd_thr[1]


def act(state):

    thresholds = {
        'BTCBUSD': [-50, 0],
        'BNBBUSD': [-100, 100],
        'LTCBUSD': [-90, 70],
        'DOGEBUSD': [-70, 0],
    }

    try:
        assert state.symbol in thresholds
    except:
        raise Exception(f"This strategy supports the following coins: {thresholds.keys()}")

    state.df_stg = _technical_analysis(state.df_stg, state.freq)

    macd_histo_norm = state.df_stg['macd_histo_norm'].iloc[-1]

    if not state.invested and _buy_signal(macd_histo_norm, thresholds[state.symbol]):
        state.invested = True
        return 'BUY'

    if state.invested and _sell_signal(macd_histo_norm, thresholds[state.symbol]):
        state.invested = False
        return 'SELL'

    return 'IDLE'
