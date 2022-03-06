import seaborn as sn
import matplotlib.pyplot as plt
import pandas as pd

#          0      1      2      3      4      5       6      7      8      9       10      11      12
coins = ['BTC', 'ETH', 'BNB', 'DOT', 'SOL', 'LUNA', 'ADA', 'CRO', 'AXS', 'SAND', 'DOGE', 'SHIB', 'MATIC']


def export_correlation_matrix(coin):
    df_x = pd.read_csv(f"s-analysis/{coin}_dfx.csv")

    sn.set(rc={'figure.figsize': (16, 8)})

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

    import pickle

    # TODO: use dataset here as well
    with open(f's-analysis/{coin}.pkl', 'rb') as f:
        data = pickle.load(f)

    EXPERIMENT_ID = data['exp_id']


    cm = df_x[cols].corr()
    hmap = sn.heatmap(cm, annot=True, cmap='coolwarm', center=0)
    plt.title(coin)
    hmap.get_figure().savefig(f"plots/{EXPERIMENT_ID}/correlation-matrix.png", bbox_inches = "tight")
    plt.close()


if __name__ == '__main__':
    # for coin in coins:
    #     print(coin)
    #     if coin not in ['CRO']:
    #         export_correlation_matrix(coin)

    export_correlation_matrix('ETH')
