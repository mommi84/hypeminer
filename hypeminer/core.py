#!/usr/bin/env python
from hypeminer import TweetStreamer, CurrencyFetcher, RobertaSentimentAnalysis, SentimentIndex


class Hypeminer(object):

    """Hypeminer object."""
    def __init__(self, currency="BTCUSDT", mov_avg_window=3):
        self.currency = currency
        self.mov_avg_window = mov_avg_window
        self.streamer = TweetStreamer()
        self.fetcher = CurrencyFetcher()
        self.rob = RobertaSentimentAnalysis()
        self.index = SentimentIndex(mov_avg_window=mov_avg_window)

    def single_run(self, n_tweets=None):

        # get tweets
        if n_tweets:
            tweets, outfile = self.streamer.stream_tweets(n_tweets=n_tweets)
        else:
            tweets, outfile = self.streamer.tweets_from_dump("20210318021353")
        print("Tweets from file {}.".format(outfile))

        # get currency value
        currency_val = self.fetcher.fetch_value(self.currency)
        print(currency_val)

        # predict sentiment
        preds = []
        for tweet in tweets:
            pred = self.rob.predict(tweet['data']['text'], show=True)
            print(pred)
            preds.append(pred)
        sentiment_val = self.index.average_sentiments(preds)
        print(sentiment_val)

        # # compute index <==== this needs a database!
        # twsa = self.index.compute(...)
        # print(twsa)




if __name__ == '__main__':
    h = Hypeminer()
    h.single_run()
