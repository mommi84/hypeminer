import math

from binance.client import Client
import configparser
import pandas as pd
from datetime import datetime

from app.strategies import compute_macd_diff_peaks, compute_macd_diff_peak_and_limit

config = configparser.ConfigParser()
config.read('config.ini')

api_key = string_val = config.get('Binance', 'api_key')
api_secret = config.get('Binance', 'api_secret')

client = Client(api_key, api_secret)

symbols = ['BNBBUSD', 'LTCBUSD', 'VETBUSD', 'DOGEBUSD']
FEES = 0.0012
ignore_orders = [115266561]  # TODO wtf


def json_to_df(obj):
    d = {k: [] for k in obj[0]}
    for o in obj:
        for k, v in o.items():
            d[k].append(v)
    return pd.DataFrame.from_dict(d)


def to_readable(epoch, millis=True):
    epoch = epoch / 1000 if millis else epoch
    return datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')


def is_ignored(order_id):
    return order_id not in ignore_orders


def get_step_size(symbol):
    for f in client.get_symbol_info(symbol)['filters']:
        if f['filterType'] == 'LOT_SIZE':
            return float(f['stepSize'])


def free_balance(asset, fees=True):
    balance = float(client.get_asset_balance(asset=asset)['free'])
    if not fees:
        return balance
    else:
        balance_after_fees = (1 - FEES) * balance
        return balance_after_fees


def buy_all_in(from_asset, to_asset, at_price):

    available_balance = free_balance(from_asset)

    print(f"Available {from_asset}: {available_balance}")

    symbol = f"{from_asset}{to_asset}"

    step_size = get_step_size(symbol)
    precision = int(round(- math.log(step_size, 10), 0))

    print(f"{from_asset} price in {to_asset}: {at_price}")

    qty = round(available_balance / at_price, precision)

    print(f"{from_asset} to buy: {qty}")

    order = client.order_market_buy(
        symbol=symbol,
        quantity=qty
    )

    return order


if __name__ == "__main__":

    from_asset, to_asset = 'BUSD', 'VET'
    strategy = 'MACDDPeaks'

    # TODO initialise data - caching

    # get current date and last x number of days before current

    while True:

        # TODO load dynamic values of take_profit stop_loss from somewhere

        orders = []
        for s in symbols:
            orders += client.get_all_orders(symbol=s)

        ticker_price = float(client.get_symbol_ticker(symbol=f"{to_asset}{from_asset}")['price'])
        print(f"current price in {ticker_price}")

        # TODO add ticker_price

        if strategy == 'MACDDPeaksLimit':
            results = {}
            for i in range(0, 11):
                thr = i / 10
                assets, bnh = compute_macd_diff_peak_and_limit(df_orig, thr, FEES)
                print((thr, assets))
                results[thr] = assets
            best_thr = sorted(results.items(), key=lambda x: x[1], reverse=True)[0][0]
            print(f"Best threshold: {best_thr}")
            compute_macd_diff_peaks(df_orig, best_thr, verbose=True, plot_chart=True)

        # buy_all_in(from_asset, to_asset, at_price=ticker_price)


