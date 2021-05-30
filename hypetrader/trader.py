#!/usr/bin/env python
import math
import pause
from datetime import datetime, timedelta
import pytz
from pprint import pprint
import sys
from tabulate import tabulate

from hypetrader.binance_bot import BinanceBot
from hypetrader.strategies import State, STRATEGY_PLANNING

from hypetrader.utilities import *


class HypeTrader(object):

    """docstring for Trader"""
    def __init__(self, crypto, fiat, strategy, freq=5, percent=1, invested=False):
        self.crypto = crypto
        self.fiat = fiat
        self.strategy = strategy
        self.freq = freq
        self.percent = percent
        self.invested = invested
        self.symbol = f"{crypto}{fiat}"
        self.bot = BinanceBot(crypto, fiat)


    def _update(self, state, update_name):
        fun = STRATEGY_PLANNING[self.strategy][update_name]
        return fun(state)


    def run(self):

        state = State()
        state.symbol = self.symbol
        state.freq = self.freq
        state.invested = self.invested

        state.iteration = 0

        order = None

        while True:

            state.candle = self.bot.get_complete_candle(self.freq)
            state.current_epoch, state.close_price = state.candle['epoch'], state.candle['close']
            state.current_dt = datetime.fromtimestamp(state.current_epoch / 1000, pytz.utc).replace(tzinfo=None)
            state.current_dt_local = datetime.fromtimestamp(state.current_epoch / 1000)

            # to run only once
            if state.iteration == 0:
                self._update(state, 'init')

            # to repeat every day (except at start)
            elif state.iteration % int(MINUTES_IN_A_DAY / self.freq) == 0:
                self._update(state, 'daily')

            # to repeat every hour (except at start of day)
            elif state.iteration % int(MINUTES_IN_AN_HOUR / self.freq) == 0:
                self._update(state, 'hourly')

            # append ticker to df
            state.df_stg = state.df_stg.append({
                'ds': to_datetime_utc(state.candle['epoch']),
                'open': state.candle['open'],
                'high': state.candle['high'],
                'low': state.candle['low'],
                'close': state.candle['close'],
                'volume': state.candle['volume'],
                'trades': state.candle['trades'],
                'macd_thr_a': state.macd_thr[0],
                'macd_thr_b': state.macd_thr[1],
            }, ignore_index=True)

            # to repeat every period
            decision = self._update(state, 'periodically')

            print(f"Iteration: {state.iteration}")
            print(f"Symbol: {state.symbol}")
            if state.best_take_profit or state.best_stop_loss:
                print(f"Last optimisation: [ best_take_profit: {state.best_take_profit}, best_stop_loss: {state.best_stop_loss} ]")
            print(f"Invested: {state.invested}")
            print(f"Decision: {decision}")

            if decision == 'BUY':
                try:
                    # order = self.bot.buy(at_price=state.close_price, perc=self.percent)
                    self._update(state, 'after_buying')
                except:
                    order = None
                    print("Order not fulfilled.")
                    state.invested = False

            elif decision == 'SELL':
                try:
                    # order = self.bot.sell(at_price=state.close_price, perc=100)
                    self._update(state, 'after_selling')
                except:
                    order = None
                    print("Order not fulfilled.")
                    state.invested = True

            else:
                order = None

            print(f"Order: {order}")

            state.df_stg.loc[state.df_stg.index[-1], 'decision'] = decision

            df_disp = state.df_stg[STRATEGY_PLANNING[self.strategy]['output_cols']].iloc[-10:]
            print(tabulate(df_disp, headers = 'keys', tablefmt = 'psql'))
            state.df_stg.to_csv(f'trader_{self.symbol}.tsv', sep='\t')

            # sleep until next iteration
            dt = state.current_dt_local + 2 * timedelta(minutes=self.freq) + timedelta(seconds=BINANCE_UPDATE_ALLOWANCE_SECONDS)
            print(f"Waiting until {dt.strftime('%Y-%m-%d %H:%M:%S')} local time...")
            sys.stdout.flush()
            pause.until(dt)

            state.iteration += 1



if __name__ == "__main__":

    trader = HypeTrader(crypto='BNB', fiat='BUSD', strategy='MACDHistoPeaks', freq=1, percent=1, invested=False)

    trader.run()
