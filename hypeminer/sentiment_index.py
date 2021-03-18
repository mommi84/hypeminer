#!/usr/bin/env python
import numpy as np


class SentimentIndex(object):

    """SentimentIndex object."""
    def __init__(self, mov_avg_window=500):
        self.mov_avg_window = mov_avg_window

    def moving_average(self, x):
        return np.convolve(x, np.ones(self.mov_avg_window), 'valid') / self.mov_avg_window

    def compute(self, data):
        twsa = {}
        for k, d in data.items():
            x = self.moving_average(d)
            twsa[k] = x
        return twsa

    def average_sentiments(self, preds):
        sentiments = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0, 'score': 0.0}
        for pred in preds:
            for k, v in pred.items():
                sentiments[k] += v
            sentiments['score'] += pred['positive'] - pred['negative']
        for k, v in sentiments.items():
            sentiments[k] = v / len(preds)
        return sentiments
