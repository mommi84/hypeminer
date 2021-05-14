#!/usr/bin/env python
from datetime import datetime, timedelta
import pandas as pd
import os
import joblib
from sklearn.metrics import plot_confusion_matrix, precision_recall_fscore_support

from hypetrader.utilities import *
from hypetrader.history import download_history_fast


THRESHOLD = 0.85

DAT_FILES = {
    'BNBBUSD': 'data/stockperceptron/BNBBUSD-20210101000000-5-90-StockPerceptron.dat',
}

feature_columns = [
    'change_norm', 'rsi14', 'rsv', 'kdj_k', 'kdj_d', 'kdj_j', 'kdj_osc', 'volume_osc', 'volume_ma3_osc', 
    'trades_osc', 'trades_ma3_osc', 'bollinger_low_norm', 'bollinger_high_norm', 'macd_histo_norm', 'macd_histo_norm_diff',
]
column_with_latest_null = 'volume_ma3_osc'


def _load_results(file):
    return joblib.load(file)


def _to_features(df, X_cols, y_col):
    
    df_not_null = df[df[column_with_latest_null].notnull()].copy()
    
    # watch for null values
    for x_col in X_cols:
#         print(f"checking: {x_col}")
        assert len(df_not_null[df_not_null[x_col].isnull()]) == 0

    return df_not_null[X_cols].copy()


def _predict(df_test, pred_id, results):
    for clax in ['is_high', 'is_low']:
        X_test = _to_features(df_test, feature_columns, clax)
        y_prob = results[clax]['model'].predict_proba(X_test)
        print(y_prob)
        y_pred = []
        for y_p in y_prob:
            y_pred.append(1 if y_p[1] > THRESHOLD else 0)
        results[clax][f'y_{pred_id}_pred'] = y_pred

    df_test_pred = df_test[df_test[column_with_latest_null].notnull()].copy()
    for clax in ['is_high', 'is_low']:
        df_test_pred[clax] = [bool(x) for x in results[clax][f'y_{pred_id}_pred']]

    return df_test_pred


def _ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()

def _rsi(data, n):
    # Make the positive gains (up) and negative gains (down) Series
    delta = data.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    # Calculate the EWMA
    roll_up1 = up.ewm(span=n).mean()
    roll_down1 = down.abs().ewm(span=n).mean()

    # Calculate the RSI based on EWMA
    rs1 = roll_up1 / roll_down1
    return 100.0 - (100.0 / (1.0 + rs1))

def _get_oscillator(data, field):
    win_50 = data[field].rolling(window=50)
    max_values = win_50.max()
    min_values = win_50.min()
    osc = []
    for max_value, min_value, value in zip(max_values, min_values, data[field]):
        if max_value == min_value:
            osc.append(50.0)
        else:
            osc.append(100.0 * (value - min_value) / (max_value - min_value))
    return osc

def _technical_analysis(df, freq):
    df['change_norm'] = 100.0 * df['close'].diff() / df['close'].shift(1)

    df['ma50'] = df['close'].rolling(window=50).mean()

    df['ema12'] = _ema(df['close'], 12)
    df['ema26'] = _ema(df['close'], 26)
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = _ema(df['macd'], 9)
    df['macd_histo'] = df['macd'] - df['signal']
    df['macd_histo_diff'] = df['macd_histo'].diff()

    boll = df['close'].rolling(window=20)
    boll_2std = 2.0 * boll.std()
    df['bollinger_low'] = boll.mean() - boll_2std
    df['bollinger_mid'] = boll.mean()
    df['bollinger_high'] = boll.mean() + boll_2std
    del boll, boll_2std

    df['rsi14'] = _rsi(df['close'], 14)

    low5 = df['low'].rolling(window=5).min()
    df['rsv'] = 100.0 * (df['close'] - low5) / (df['high'].rolling(window=5).max() - low5)
    del low5
    df.loc[df['rsv'].isnull(), 'rsv'] = 50 # when max=min, the RSV is halfway up
    df['kdj_k'] = df['rsv'].rolling(window=3).mean()
    df['kdj_d'] = df['kdj_k'].rolling(window=3).mean()
    df['kdj_j'] = 3.0 * df['kdj_k'] - 2.0 * df['kdj_d']

    df['kdj_osc'] = 100.0 - abs(df['kdj_k'] - df['kdj_d']) # crosses at 99-100

    df['volume_ma3'] = df['volume'].rolling(window=3).sum() # accumulated volumes
    df['volume_osc'] = _get_oscillator(df, 'volume')
    df['volume_ma3_osc'] = _get_oscillator(df, 'volume_ma3')

    df['trades_ma3'] = df['trades'].rolling(window=3).sum() # accumulated trades
    df['trades_osc'] = _get_oscillator(df, 'trades')
    df['trades_ma3_osc'] = _get_oscillator(df, 'trades_ma3')

    df['bollinger_low_norm'] = 200.0 - 100.0 * df['low'] / df['bollinger_low'] # breaks above 100
    df['bollinger_high_norm'] = 100.0 * df['high'] / df['bollinger_high']      # breaks above 100

    df['macd_histo_norm'] = 100000.0 * df['macd_histo'] / df['ma50'] / freq    # ideally in [-100, +100]
    df['macd_histo_norm_diff'] = df['macd_histo_norm'].diff()

    return df


def initialise(state):

    dat_file = DAT_FILES[state.symbol]
    if not os.path.isfile(dat_file):
        raise Exception(f"Model file not found: {dat_file}")
    state.model_data = _load_results(dat_file)
    print(f"Loaded file {dat_file}.")

    freq = state.freq
    symbol = state.symbol

    # initialise data: get current date and last x number of days before current (TODO caching)
    past_start_time = (datetime.utcnow() - timedelta(days=60) - 2 * timedelta(minutes=freq)).strftime('%Y%m%d%H%M%S')
    df = download_history_fast(symbol, past_start_time, freq=freq, days=60)

    # remove last row as it is added periodically
    state.df_stg = df.iloc[:-1].copy()


def act(state):

    state.df_stg = _technical_analysis(state.df_stg, state.freq)

    state.df_stg = _predict(state.df_stg, 'live', state.model_data)
    print(state.df_stg)

    prediction = '----'
    if state.df_stg['is_high'].iloc[-1] == True:
        prediction = 'high'
    elif state.df_stg['is_low'].iloc[-1] == True:
        prediction = 'low'

    if not state.invested and prediction == 'low':
        state.invested = True
        return 'BUY'

    if state.invested and prediction == 'high':
        state.invested = False
        return 'SELL'

    return 'IDLE'
