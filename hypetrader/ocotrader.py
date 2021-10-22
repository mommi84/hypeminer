# import math
import pause
from datetime import datetime, timedelta
import pytz
# from pprint import pprint
import sys
# from tabulate import tabulate
import numpy as np

from hypetrader.binance_bot import BinanceBot
from hypetrader.history import download_history_fast_ocotrader

from hypetrader.utilities import *


def ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()

def normalise(df_orig, freq):
    df = df_orig.copy()
    
    fields = list(df)
    
    for field in fields:
        if field in ['volume', 'trades']:
            for ma in [1, 3, 9]:
                df[f"{field}_pm_ma{ma}"] = df[field].rolling(window=ma).mean() / freq
        else:
            if field != 'close':
                df[f"{field}_norm"] = df[field] / df['close']

        if field != 'close':
            df.drop(field, axis=1, inplace=True)
    
    for x in [50, 200]:
        df[f"close_ma{x}_norm"] = df['close'].rolling(window=x).mean() / df['close']
    
    for x in [12, 26]:
        df[f"close_ema{x}_norm"] = ema(df['close'], x) / df['close']
    
    return df

def is_good_signal(X, Y, decfun=False):
    Tx = -0.809
    Ty = -0.234
    F = (12*(X+Tx) - 3*(Y+Ty))**2 + (X+Tx) + (Y+Ty) - 1
    return F if decfun else F >= 0


def main():

    freq = 1
    crypto = 'BNB'
    fiat = 'BUSD'
    symbol = f"{crypto}{fiat}"
    stop_loss = 0.97
    take_profit = 1.02

    bot = BinanceBot(crypto, fiat)


    while True:

        current_dt_local = datetime.now()
        try:
            df = download_history_fast_ocotrader(symbol, (
                datetime.now() - timedelta(minutes=200)).strftime('%Y%m%d%H%M%S'), freq=1, days=0.25)
        except Exception as e:
            print(e)
            continue

        df_n = normalise(df, freq)
        df_n = df_n[['close', 'close_ema26_norm', 'close_ma200_norm']].dropna()
        try:
            df_n['buy_signal'] = np.vectorize(is_good_signal)(df_n['close_ema26_norm'], df_n['close_ma200_norm'])
        except ValueError as e:
            print(e)
            continue
        print("")
        print(df_n)

        if df_n.iloc[-1]['buy_signal']:
            print("Suggestion: BUY")

            try:
                price = bot.get_ticker_price()
                buy_order = bot.buy(price, perc=99)
                print(buy_order)

                sell_order = bot.sell_stop_limit(price * stop_loss, price * take_profit, perc=100)
                print(sell_order)
            except Exception as e:
                print(e)
                print(f"An order might be already in place. Skipping this buy signal.")

        else:
            print("Suggestion: IDLE")

        # sleep until next iteration
        dt = df.index[-1] + timedelta(minutes=freq) + timedelta(seconds=59)
        print(f"Waiting until {dt.strftime('%Y-%m-%d %H:%M:%S')} local time...")
        sys.stdout.flush()
        pause.until(dt)


if __name__ == '__main__':
    main()
