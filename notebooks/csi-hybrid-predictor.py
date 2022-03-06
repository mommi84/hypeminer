#!/usr/bin/env python
# coding: utf-8

# In[81]:


#          0      1      2      3      4      5       6      7      8      9       10      11      12
coins = ['BTC', 'ETH', 'BNB', 'DOT', 'SOL', 'LUNA', 'ADA', 'CRO', 'AXS', 'SAND', 'DOGE', 'SHIB', 'MATIC']


# In[82]:


from hypecommons import download_history_fast
import pandas as pd
import re
import os

def run_data_preprocessing(coin, dataset='001'):

    START_TIME = '2021-12-16 01:00:00'
    BASE = 'BUSD'
    MOV_AVG_PERIODS = 24 * 3
    HOURS_AHEAD = MOV_AVG_PERIODS

    # sentiment analysis indices
    df_i = pd.read_csv(f"s-analysis/indices-{coin}-{dataset}.csv")
    if coin in ['BTC', 'ETH']: # previous format
        df_i['dt'] = pd.date_range(start=START_TIME, periods=len(df_i), freq='1H')
    else:
        df_i['dt'] = pd.to_datetime(df_i['dt'])
    df_i = df_i.set_index('dt')

    EXPERIMENT_ID = f"{coin}-{BASE}-{MOV_AVG_PERIODS}ma-{HOURS_AHEAD}h-{df_i.index[-1].strftime('%Y%m%d%H%M%S')}"
    os.makedirs(f"plots/{EXPERIMENT_ID}", exist_ok=True)


    # In[83]:


    for col in df_i:
    #     df_i[col] = (df_i[col] - df_i[col].mean()) / df_i[col].std()
        df_i[f"sent/{col}"] = df_i[col].rolling(window=MOV_AVG_PERIODS).mean()
        df_i.drop(col, inplace=True, axis=1)

    # price history
    df_h = download_history_fast(f"{coin}{BASE}", re.sub("[^0-9]", "", START_TIME), days=(len(df_i)+HOURS_AHEAD)/24)
    for col in ['open', 'high', 'low']:
        df_h.drop(col, inplace=True, axis=1)
    for col in df_h:
        df_h[f"tech/{col}"] = df_h[col]
        df_h.drop(col, inplace=True, axis=1)

    df = df_h.join(df_i)


    # In[84]:


    df_gt = pd.DataFrame()
    df_gt_orig = pd.read_csv('google-trends/training.csv')
    df_gt['google/trends'] = df_gt_orig[coin] / 100
    df_gt['date'] = pd.to_datetime(df_gt_orig['date'])
    df_gt = df_gt.set_index('date')

    df_gt = df_gt.resample('1H').ffill()
    df_gt['google/trends'] = df_gt['google/trends'].shift(24)
    df_gt.dropna(inplace=True)

    df = df.join(df_gt)


    # In[85]:


    df_tc = pd.read_csv(f"tweet-counts/joined-{coin}.csv")
    df_tc['end'] = pd.to_datetime(df_tc['end'])
    df_tc['twitter/count'] = df_tc['tweet_count']
    df_tc = df_tc.set_index('end').tz_localize(None)
    df_tc.drop(['start', 'tweet_count'], axis=1, inplace=True)
    df = df.join(df_tc)


    # In[86]:


    import matplotlib.pyplot as plt

    plt.rcParams["figure.figsize"] = (16, 4)

    df_sent = df[['sent/positive', 'sent/greedy', 'sent/fearful', 'tech/close']].dropna()

    ax = df_sent[['sent/positive', 'sent/greedy', 'sent/fearful']].plot(title=coin)
    ax.xaxis.label.set_visible(False)
    plt.legend(loc='best')
    plt.close()

    plt.clf()
    ax = df_sent['tech/close'].dropna().plot(title=f"{coin}/{BASE}")
    ax.xaxis.label.set_visible(False)
    plt.legend(loc='best')
    plt.savefig(f"plots/{EXPERIMENT_ID}/price.png", bbox_inches = "tight")
    plt.close()


    # In[87]:


    def ema(data, n):
        alpha = 2 / (1 + n)
        return data.ewm(alpha=alpha, adjust=False).mean()

    def rsi(data, n):
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
        return 1.0 - (1.0 / (1.0 + rs1))

    def technical_analysis(df):
        macd = ema(df['tech/close'], 12) - ema(df['tech/close'], 26)
        df['techan/macd_norm'] = macd / df['tech/close']
        df['techan/macd_histo_norm'] = (macd - ema(macd, 9)) / df['tech/close']

        boll = df['tech/close'].rolling(window=20)
        boll_2std = 2.0 * boll.std()
        df['techan/bollinger_low_score'] = df['tech/close'] / (boll.mean() - boll_2std)
        df['techan/bollinger_mid_score'] = df['tech/close'] / (boll.mean())
        df['techan/bollinger_high_score'] = df['tech/close'] / (boll.mean() + boll_2std)
        del boll, boll_2std

        df['techan/rsi14'] = rsi(df['tech/close'], 14)
        
        return df


    # In[88]:


    df_x = df.copy()
    df_x = technical_analysis(df_x)

    for col in ['tech/volume', 'tech/trades', 'twitter/count']:
        # TODO calculate MAX over the training set, not the full set
        df_x[col] = df_x[col] / df_x[col].max()
        df_x[f"{col}_osc_ma"] = df_x[col].rolling(window=MOV_AVG_PERIODS).mean()

    df_x['tech/change'] = df_x['tech/close'].diff(HOURS_AHEAD) / df_x['tech/close'].shift(HOURS_AHEAD) * 100

    df_x['future_change'] = (-df_x['tech/close'].diff(-HOURS_AHEAD) / df_x['tech/close']) * 100
    ax = df_x.dropna()[::12]['future_change'].plot.bar(title=f"{coin}/{BASE}")
    ax.xaxis.label.set_visible(False)
    plt.legend(loc='best')

    df_x.dropna(inplace=True)


    # In[89]:


    # from sklearn.linear_model import LinearRegression
    # from IPython.display import display

    cols = list(df_i) \
        + ['tech/change', 'tech/volume_osc_ma', 'tech/trades_osc_ma'] \
        + ['techan/macd_norm', 'techan/macd_histo_norm', 'techan/rsi14'] \
        + ['techan/bollinger_low_score', 'techan/bollinger_mid_score', 'techan/bollinger_high_score'] \
        + ['google/trends', 'twitter/count_osc_ma'] \

    # X = df_x[cols]
    # y = df_x['future_change']

    # model_full = LinearRegression().fit(X, y)
    # print(f"Train score: {model_full.score(X, y)}")

    # plt.rcParams["figure.figsize"] = (16, 4)

    # ax = df_x[['sent/positive', 'sent/hopeful', 'sent/enthusiastic']].plot(title=coin)
    # ax.xaxis.label.set_visible(False)
    # plt.legend(loc='best')
    # plt.close()


    # In[90]:

    df_x.to_csv(f"s-analysis/{coin}_dfx.csv")



    # ## Split into train & test, run first simulation

    # In[91]:


    train_size = int(0.7 * len(df_x))

    df_train = df_x[:train_size].copy()
    df_test = df_x[train_size:].copy()

    X = df_train[cols]
    y = df_train['future_change']


    # In[92]:


    X_test = df_test[cols]
    y_test = df_test['future_change']


    # In[93]:


    export = {'exp_id': EXPERIMENT_ID, 'X_train': X, 'y_train': y, 'X_test': X_test, 'y_test': y_test}

    import pickle
    with open(f's-analysis/{coin}.pkl', 'wb') as f_out:
        pickle.dump(export, f_out)


if __name__ == '__main__':
    # for coin in coins:
    #     print(coin)
    #     if coin not in ['CRO']:
    #         run_data_preprocessing(coin)

    run_data_preprocessing('ETH', dataset='004')
