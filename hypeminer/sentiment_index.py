#!/usr/bin/env python
import numpy as np
import pandas as pd


class SentimentIndex(object):

    """SentimentIndex object."""
    def __init__(self, mov_avg_window=5):
        self.mov_avg_window = mov_avg_window

    def moving_average(self, x):
        return np.convolve(x, np.ones(self.mov_avg_window), 'valid') / self.mov_avg_window

    def compute(self, data):
        twsa = {}
        for k, d in data.items():
            x = self.moving_average(d)
            twsa[k] = x
        return twsa

    def index_average(self, index_store):
        df = pd.read_csv(index_store, sep='\t')
        last_n = df.tail(self.mov_avg_window)
        avg = last_n.mean()
        return {k: avg.loc[k] for k in list(avg.index)}

    def sample_average(self, preds):
        sentiments = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0, 'score': 0.0}
        for pred in preds:
            for k, v in pred.items():
                sentiments[k] += v
            sentiments['score'] += pred['positive'] - pred['negative']
        for k, v in sentiments.items():
            sentiments[k] = v / len(preds)
        return sentiments

if __name__ == '__main__':
    si = SentimentIndex()
    avg = si.index_average("data/BTCUSDT/indices/20210318132039.tsv")
    print(avg)