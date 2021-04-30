#!/usr/bin/env python
import math
import pause
from datetime import datetime, timedelta
import pytz

from hypetrader.binance_bot import BinanceBot
from hypetrader.strategies import State, STRATEGY_PLANNING

from hypetrader.utilities import *


class HypeTrader(object):

    """docstring for Trader"""
    def __init__(self, crypto, fiat, strategy, freq=5):
        self.crypto = crypto
        self.fiat = fiat
        self.strategy = strategy
        self.freq = freq
        self.symbol = f"{crypto}{fiat}"
        self.bot = BinanceBot(crypto, fiat)


    def run(self):

        state = State()
        state.symbol = self.symbol
        state.freq = self.freq
        state.invested = False

        state.iteration = 0

        while True:

            state.current_epoch, state.open_price = self.bot.get_candle(self.freq)
            state.current_dt = datetime.fromtimestamp(state.current_epoch / 1000, pytz.utc).replace(tzinfo=None)
            state.current_dt_local = datetime.fromtimestamp(state.current_epoch / 1000)

            # to repeat every day
            if state.iteration % int(MINUTES_IN_A_DAY / self.freq) == 0:

                daily_update = STRATEGY_PLANNING[self.strategy]['daily']
                daily_update(state)

            # to repeat every hour
            if state.iteration % int(MINUTES_IN_AN_HOUR / self.freq) == 0:

                hourly_update = STRATEGY_PLANNING[self.strategy]['hourly']
                hourly_update(state)

            # append ticker to df
            state.df_stg = state.df_stg.append({'ds': state.current_dt, 'open': state.open_price}, ignore_index=True)

            # to repeat every period
            periodic_update = STRATEGY_PLANNING[self.strategy]['periodically']
            decision = periodic_update(state)

            print(f"Iteration {state.iteration}: {decision}")

            if decision == 'BUY':
                order = self.bot.buy(at_price=state.open_price, perc=1)
            elif decision == 'SELL':
                order = self.bot.sell(at_price=state.open_price, perc=1)
            else:
                order = None

            print(f"Order: {order}")

            state.df_stg.loc[state.df_stg.index[-1], 'decision'] = decision

            print(state.df_stg[['ds', 'open', 'suggest', 'limit', 'decision']])
            state.df_stg.to_csv(f'trader_{self.symbol}.tsv', sep='\t')

            # sleep until next iteration
            dt = state.current_dt_local + timedelta(minutes=self.freq) + timedelta(seconds=BINANCE_UPDATE_ALLOWANCE_SECONDS)
            print(f"Waiting until {dt.strftime('%Y-%m-%d %H:%M:%S')} local time...")
            pause.until(dt)

            state.iteration += 1



if __name__ == "__main__":

    crypto, fiat, strategy = 'BNB', 'BUSD', 'MACDDiffAdaptivePeakAndLimit'

    trader = HypeTrader(crypto, fiat, strategy, freq=1)

    trader.run()
