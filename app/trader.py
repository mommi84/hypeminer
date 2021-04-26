#!/usr/bin/env python
import math

from app.binance_interface import BinanceInterface
from app.strategies import *
from app.utilities import *


class Trader(object):

    """docstring for Trader"""
    def __init__(self, crypto, fiat, strategy='MACDDiffAdaptivePeakAndLimit'):
        self.crypto = crypto
        self.fiat = fiat
        self.strategy = strategy
        self.binance_i = BinanceInterface(crypto, fiat)


    def run(self):

        # TODO initialise data - caching

        # get current date and last x number of days before current

        while True:

            # TODO load dynamic values of take_profit stop_loss from somewhere


            ticker_price = self.binance_i.get_ticket_price()
            print(f"current price: {ticker_price}")

            # TODO add ticker_price

            if strategy == 'MACDDiffAdaptivePeakAndLimit':
                results = {}
                for i in range(0, 11):
                    thr = i / 10
                    assets, bnh = compute_macd_diff_peak_and_limit(df_orig, thr, FEES)
                    print((thr, assets))
                    results[thr] = assets
                best_thr = sorted(results.items(), key=lambda x: x[1], reverse=True)[0][0]
                print(f"Best threshold: {best_thr}")
                compute_macd_diff_peaks(df_orig, best_thr, verbose=True, plot_chart=True)

            # self.binance_i.buy_all_in(at_price=ticker_price)

            # sleep 5 or less minutes



if __name__ == "__main__":

    crypto, fiat = 'VET', 'BUSD'

    trader = Trader(crypto, fiat)

    trader.run()
