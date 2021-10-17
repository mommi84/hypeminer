#!/usr/bin/env python
# coding: utf-8

# In[7]:


#!/usr/bin/env python
from binance.client import Client
import configparser
import math


class BinanceBot(object):

    """docstring for BinanceInterface"""
    def __init__(self, crypto, fiat):
        self.crypto = crypto
        self.fiat = fiat
        self.symbol = "{crypto}{fiat}".format(crypto=crypto, fiat=fiat)
        self.configure()

    def configure(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        api_key = config.get('Binance', 'api_key')
        api_secret = config.get('Binance', 'api_secret')
        self.client = Client(api_key, api_secret)

    def get_all_orders(self):
        return self.client.get_all_orders(symbol=self.symbol)

    def get_ticker_price(self):
        return float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])


bot = BinanceBot('BNB', 'BUSD')


# In[8]:


from datetime import datetime, timezone, timedelta
import pandas as pd

data = bot.get_all_orders()
df = pd.DataFrame(data)


# In[9]:

import json
import pytz

df['dt'] = pd.to_datetime(df['updateTime'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Europe/London')
df.set_index('dt', inplace=True)

df['cummulativeQuoteQty'] = df['cummulativeQuoteQty'].map(float)
df['executedQty'] = df['executedQty'].map(float)

# print(df)

start_time = datetime(2021, 9, 20, tzinfo=pytz.timezone('Europe/London'))

df_work = df[
    (df['clientOrderId'] != 'VByDxroeamwmP89ZvgzCYa') & 
    (df.index >= start_time) & 
    (df['status'] == 'FILLED')
].copy()

ticker = bot.get_ticker_price()

open_pos = len(df_work[df_work['side'] == 'SELL']) != len(df_work[df_work['side'] == 'BUY'])

if open_pos:
    buys = df_work[df_work['side'] == 'BUY']
    last_buy = round(buys['cummulativeQuoteQty'].iloc[-1] / buys['executedQty'].iloc[-1], 1)
    open_pos_trend_perc = round((ticker - last_buy) / last_buy * 100, 1)
else:
    last_buy = None
    open_pos_trend_perc = None

# In[10]:



df_plot = df_work[
    df_work['side'] == 'SELL'
][['cummulativeQuoteQty']]

its_now = pd.DataFrame(
    [[df_plot.iloc[-1]['cummulativeQuoteQty']]], 
    columns=['cummulativeQuoteQty'],
    index=[datetime.now(pytz.timezone('Europe/London'))]
)

df_plot = df_plot.append(its_now)

stake = df_plot.iloc[0]['cummulativeQuoteQty']

df_plot['cummulativeQuoteQty'] = (df_plot['cummulativeQuoteQty']) / stake


# In[18]:


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as plticker

plt.style.use('ggplot')
plt.rcParams["figure.figsize"] = (10, 6)

axes = plt.gca()

axes.xaxis.set_major_formatter(mdates.DateFormatter('%d %b\n%H:%M'))

loc = plticker.MultipleLocator(base=0.01)
axes.yaxis.set_major_locator(loc)

# df_plot = df_plot[df_plot.index >= datetime.now(tz=pytz.timezone('Europe/London')) - timedelta(days=14)]

plt.plot(df_plot.index, df_plot['cummulativeQuoteQty'], label='assets', drawstyle='steps-post')

plt.legend(loc="best", prop={'size': 12})

plt.savefig('assets.png')


# In[ ]:

assets = round(df_plot['cummulativeQuoteQty'].iloc[-1], 2)
assets_perc = int((df_plot['cummulativeQuoteQty'].iloc[-1] - 1) * 100)

months_since_start = (df_plot.index[-1] - start_time).total_seconds() / (3600*24*30)
apy = round(assets ** (12 / months_since_start), 2)
apy_perc = int((assets ** (12 / months_since_start) - 1) * 100)


trader_info = {
    'timestamp': datetime.now(pytz.timezone('Europe/London')).strftime("%Y-%m-%d %H:%M:%S"),
    'open_pos': open_pos,
    'open_pos_trend_perc': open_pos_trend_perc,
    'last_buy': last_buy,
    'ticker': ticker,
    'assets': assets,
    'assets_perc': assets_perc,
    'apy': apy,
    'apy_perc': apy_perc,
}

with open('trader_info.json', 'w') as f_out:
    json.dump(trader_info, f_out)



