#!/usr/bin/env python
# coding: utf-8

# In[124]:


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout

import os

# In[125]:


#          0      1      2      3      4      5       6      7      8      9       10      11      12
coins = ['BTC', 'ETH', 'BNB', 'DOT', 'SOL', 'LUNA', 'ADA', 'CRO', 'AXS', 'SAND', 'DOGE', 'SHIB', 'MATIC']


# In[126]:



def run_model_training(coin, timesteps=6, units=500, lr=0.00002, n_epochs=2000):

    # In[127]:


    import pickle
    import numpy as np

    with open(f's-analysis/{coin}.pkl', 'rb') as f:
        data = pickle.load(f)

    EXPERIMENT_ID = data['exp_id']
    X_train = data['X_train'].to_numpy()
    y_train = data['y_train']
    X_test = data['X_test'].to_numpy()
    y_test = data['y_test']

    print(EXPERIMENT_ID, X_train.shape, y_train.shape, X_test.shape, y_test.shape)
    os.makedirs(f"plots/{EXPERIMENT_ID}", exist_ok=True)


    # In[128]:


    from sklearn.preprocessing import MinMaxScaler

    scaler = MinMaxScaler(feature_range=(0, 1))
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.fit_transform(X_test)


    # In[129]:


    def time_window(input_data):
        out = []
        for i in range(len(input_data)):
            m = input_data[i : i + timesteps, :]
            if len(m) == timesteps:
                out.append(m)
        return np.array(out)

    X_train = time_window(X_train)
    X_test = time_window(X_test)

    y_train = y_train[timesteps-1:]
    y_test = y_test[timesteps-1:]

    print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)


    # In[144]:


    from tensorflow.keras import optimizers
        
    model = Sequential()
    model.add(LSTM(units, input_shape=(X_train.shape[1], X_train.shape[2])))
    # model.add(LSTM(32, return_sequences=True))
    model.add(Dropout(0.2))
    # model.add(LSTM(250))
    # model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(loss='mae', optimizer=optimizers.Adam(lr=lr))

    history = model.fit(X_train, y_train, epochs=n_epochs, batch_size=100, validation_data=(X_test, y_test), 
                        verbose=1, shuffle=False)


    # In[145]:


    import matplotlib.pyplot as plt

    plt.style.use('ggplot')
    plt.rcParams["figure.figsize"] = (16, 4)

    plt.plot(history.history['loss'], label='train')
    plt.plot(history.history['val_loss'], label='test')
    plt.legend()
    plt.title(f"{coin} :: LSTM Predictor Loss")
    plt.savefig(f"plots/{EXPERIMENT_ID}/losses.png", bbox_inches = "tight")
    plt.close()


    # In[146]:


    #prediction on training and testing data
    train_predict = model.predict(X_train)    
    test_predict = model.predict(X_test)       

    inv_train_predict = np.concatenate((train_predict, X_train[:,-1,:]), axis=1)
    inv_test_predict = np.concatenate((test_predict, X_test[:,-1,:]), axis=1)


    # In[147]:


    y_test[timesteps-1:].shape


    # In[148]:


    import pandas as pd
    plt.rcParams["figure.figsize"] = (16, 4)

    df = pd.DataFrame(y_test)

    df['lstm_predicted'] = inv_test_predict[:,0]

    ax = df[::6].plot.bar(title=f"{coin} :: LSTM Predictor")
    ax.set_ylabel(f"% change after 72 hours")
    plt.savefig(f"plots/{EXPERIMENT_ID}/predictor-test-bars.png", bbox_inches = "tight")
    plt.close()


    # In[149]:


    plt.rcParams["figure.figsize"] = (16, 4)

    plt.plot(df.index, [0] * len(df), c='k', linestyle='--', alpha=0.5)
    ax = df.plot(title=f"{coin} :: LSTM Predictor", ax=plt.gca())
    ax.set_ylabel(f"% change after 72 hours")
    plt.savefig(f"plots/{EXPERIMENT_ID}/predictor-test-line.png", bbox_inches = "tight")
    plt.close()


    # In[150]:


    import pandas as pd

    df = pd.DataFrame(y_train)

    df['lstm_predicted'] = inv_train_predict[:,0]

    ax = df[::12].plot.bar(title=f"{coin} :: LSTM Predictor (training)")
    ax.set_ylabel(f"% change after 72 hours")
    plt.savefig(f"plots/{EXPERIMENT_ID}/predictor-training-bars.png", bbox_inches = "tight")
    plt.close()


    # In[151]:


    from sklearn.feature_selection import f_regression, SelectKBest

    X_train_orig = data['X_train'].to_numpy()
    y_train_orig = data['y_train']

    cols = ['sent/positive',
     'sent/negative',
     'sent/enthusiastic',
     'sent/confused',
     'sent/angry',
     'sent/sad',
     'sent/greedy',
     'sent/fearful',
     'sent/shocked',
     'sent/hopeful',
     'sent/indifferent',
     'sent/sarcastic',
     'tech/change',
     'tech/volume_osc_ma',
     'tech/trades_osc_ma',
     'techan/macd_norm',
     'techan/macd_histo_norm',
     'techan/rsi14',
     'techan/bollinger_low_score',
     'techan/bollinger_mid_score',
     'techan/bollinger_high_score',
     'google/trends',
     'twitter/count_osc_ma']

    # configure to select all features
    fs = SelectKBest(score_func=f_regression, k=10)
    # learn relationship from training data
    fs.fit(X_train_orig, y_train_orig)

    # what are scores for the features
    df_feat = pd.DataFrame(
        [{'feature': col, 'score': fs.scores_[i] / max(fs.scores_)} for i, col in enumerate(cols)]
    ).sort_values(by='score', ascending=False)


    # In[152]:


    # plot the scores
    plt.rcParams["figure.figsize"] = (12, 12)
    plt.barh(df_feat['feature'], df_feat['score'])
    plt.yticks(fontsize=14)
    plt.gca().invert_yaxis()
    plt.title(f"{coin} :: Feature Importance")
    plt.savefig(f"plots/{EXPERIMENT_ID}/features.png", bbox_inches = "tight")
    plt.close()


if __name__ == '__main__':
    # for coin in coins:
    #     print(coin)
    #     if coin not in ['CRO']:
    #         run_model_training(coin) # TODO: lr as parameter

    run_model_training('ETH', timesteps=6, units=128, lr=0.00001, n_epochs=1000)

# TODO: save network hyperparameters + input tensor timesteps

