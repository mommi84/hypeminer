#!/usr/bin/env python
# coding: utf-8

# In[14]:


from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import numpy as np

SYMBOL = 'BNBBUSD'
FREQ = 1

from hypecommons import download_history_fast

def ema(data, n):
    alpha = 2 / (1 + n)
    return data.ewm(alpha=alpha, adjust=False).mean()

def normalise(df_orig):
    df = df_orig.copy()
    
    fields = list(df)
    
    for field in fields:
        if field in ['volume', 'trades']:
            for ma in [1, 3, 9]:
                df[f"{field}_pm_ma{ma}"] = df[field].rolling(window=ma).mean() / FREQ
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

HOURS = 9

df = download_history_fast(SYMBOL, (
    datetime.now() - timedelta(minutes=HOURS*60+200)).strftime('%Y%m%d%H%M%S'), freq=FREQ, days=1)

df_n = normalise(df)

plt.figure(figsize=(6, 6))

palette = plt.rcParams['axes.prop_cycle'].by_key()['color']
to_col = {1: 'buy signal', 0: 'idle'}

delta = 0.001
xy_min, xy_max = 0.9, 1.1
xrange = np.arange(xy_min, xy_max, delta)
yrange = np.arange(xy_min, xy_max, delta)
X, Y = np.meshgrid(xrange,yrange)
F = is_good_signal(X, Y, decfun=True)
plt.contour(X, Y, F, [0], colors=palette[2], linewidths=1)

n_datapoints = HOURS * 60
df_asd = df_n.copy().iloc[-n_datapoints:]
# n_datapoints = len(df_asd)
df_asd['buy_signal'] = np.vectorize(is_good_signal)(df_asd['close_ema26_norm'], df_asd['close_ma200_norm'])
colour = []
for i, (index, row) in enumerate(df_asd.iterrows()):
    level = f"{50+int((i/n_datapoints)**(5)*206):02x}"
    if row['buy_signal'] == False:
        colour.append(f'#{level}0000')
    else:
        colour.append(f'#0000{level}')

print(df_asd[df_asd['buy_signal'] == True])

df_asd['colour'] = colour

for c, cl in to_col.items():
    dfx_asd = df_asd[df_asd['buy_signal'] == c]
    plt.scatter(dfx_asd['close_ema26_norm'], dfx_asd['close_ma200_norm'], s=15, c=dfx_asd['colour'], label=cl)

plt.legend(loc="best")
plt.title(f"Signal classification — Last {HOURS} hours")

xy_min, xy_max = 0.95, 1.05
plt.gca().set_xlim([xy_min, xy_max])
plt.gca().set_ylim([xy_min, xy_max])
plt.xlabel('close_ema26_norm')
plt.ylabel('close_ma200_norm')
# plt.show()

plt.savefig('signal-classification.png')


# In[ ]:

import json
import pytz

sgnl_info = {
    'timestamp': datetime.now(pytz.timezone('Europe/London')).strftime("%Y-%m-%d %H:%M:%S"),
    'sgnl': round((is_good_signal(df_asd['close_ema26_norm'].iloc[-1], df_asd['close_ma200_norm'].iloc[-1], decfun=True) + 0.1) / 0.1, 2),
}

with open('sgnl_info.json', 'w') as f_out:
    json.dump(sgnl_info, f_out)



