#!/usr/bin/env python
import math
import pause
from datetime import datetime, timedelta
import pytz
from pprint import pprint

from hypetrader.binance_bot import BinanceBot
from hypetrader.strategies import State, STRATEGY_PLANNING

from hypetrader.utilities import *


class HypeTrader(object):

    """docstring for Trader"""
    def __init__(self, crypto, fiat, strategy, freq=5, percent=1):
        self.crypto = crypto
        self.fiat = fiat
        self.strategy = strategy
        self.freq = freq
        self.percent = percent
        self.symbol = f"{crypto}{fiat}"
        self.bot = BinanceBot(crypto, fiat)


    def _update(self, state, update_name):
        fun = STRATEGY_PLANNING[self.strategy][update_name]
        return fun(state)


    def run(self):

        state = State()
        state.symbol = self.symbol
        state.freq = self.freq
        state.invested = False

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

            # to repeat every day
            if state.iteration % int(MINUTES_IN_A_DAY / self.freq) == 0:
                self._update(state, 'daily')

            # to repeat every hour
            if state.iteration % int(MINUTES_IN_AN_HOUR / self.freq) == 0:
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
            }, ignore_index=True)

            # to repeat every period
            decision = self._update(state, 'periodically')

            print(f"Iteration: {state.iteration}")
            print(f"Last optimisation: [ best_take_profit: {state.best_take_profit}, best_stop_loss: {state.best_stop_loss} ]")
            print(f"Invested: {state.invested}")
            print(f"Decision: {decision}")

            if decision == 'BUY':
                order = self.bot.buy(at_price=state.close_price, perc=self.percent)
                self._update(state, 'after_buying')

            elif decision == 'SELL':
                order = self.bot.sell(at_price=state.close_price, perc=self.percent)
                self._update(state, 'after_selling')

            else:
                order = None

            print(f"Order: {order}")

            state.df_stg.loc[state.df_stg.index[-1], 'decision'] = decision

            print(state.df_stg[STRATEGY_PLANNING[self.strategy]['output_cols']])
            state.df_stg.to_csv(f'trader_{self.symbol}.tsv', sep='\t')

            # sleep until next iteration
            dt = state.current_dt_local + timedelta(minutes=self.freq) + timedelta(seconds=BINANCE_UPDATE_ALLOWANCE_SECONDS)
            print(f"Waiting until {dt.strftime('%Y-%m-%d %H:%M:%S')} local time...")
            pause.until(dt)

            state.iteration += 1

            with open('decision.log.txt', 'a') as f_out:
                f_out.write(f"{state.current_dt_local}\t{state.close_price}\t{decision}\n")



if __name__ == "__main__":

    crypto, fiat, strategy = 'BNB', 'BUSD', 'StockPerceptron'

    trader = HypeTrader(crypto, fiat, strategy, freq=5, percent=1)

    trader.run()
