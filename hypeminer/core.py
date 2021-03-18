#!/usr/bin/env python
from hypeminer import TweetStreamer, CurrencyFetcher, RobertaSentimentAnalysis, SentimentIndex, MultivariateTSF
import os.path


SAMPLES_STORE = 'data/{}/samples/{}.tsv'
INDICES_STORE = 'data/{}/indices/{}.tsv'


class Hypeminer(object):

    """Hypeminer object."""
    def __init__(self, store_id, currency='BTCUSDT', target='currency', regressors=['score', 'negative'], mov_avg_window=5, forecast_days=4):
        self.store_id = store_id
        self.currency = currency
        self.target = target
        self.regressors = regressors
        self.mov_avg_window = mov_avg_window
        self.forecast_days = forecast_days
        self.streamer = TweetStreamer(currency)
        self.fetcher = CurrencyFetcher()
        self.rob = RobertaSentimentAnalysis()
        self.index = SentimentIndex(mov_avg_window=mov_avg_window)
        self.multivar = MultivariateTSF(currency, forecast_days, target, regressors)
        self.prepare_stores()

    def prepare_stores(self):
        self.samples_store = SAMPLES_STORE.format(self.currency, self.store_id)
        self.indices_store = INDICES_STORE.format(self.currency, self.store_id)

        for store in [self.samples_store, self.indices_store]:
            if not os.path.isfile(store):
                with open(store, 'w') as f_out:
                    f_out.write("{}\t{}\t{}\t{}\t{}\t{}\n"
                        .format("timestamp", "currency", "positive", "neutral", "negative", "score"))

    def pipeline(self, tweets, timestamp):
        # download currency value
        currency_val = self.fetcher.fetch_value(self.currency)
        print(currency_val)

        # predict sentiment
        preds = []
        for tweet in tweets:
            pred = self.rob.predict(tweet['data']['text'], show=True)
            print(pred)
            preds.append(pred)

        # compute sample average and store values
        sample_val = self.index.sample_average(preds)
        print(sample_val)
        with open(self.samples_store, 'a') as f_out:
            f_out.write("{}\t{}\t{}\t{}\t{}\t{}\n"
                .format(timestamp, currency_val["value"], sample_val["positive"], 
                    sample_val["neutral"], sample_val["negative"], sample_val["score"]))

        # compute index average within window and save values
        index_val = self.index.index_average(self.samples_store)
        with open(self.indices_store, 'a') as f_out:
            f_out.write("{}\t{}\t{}\t{}\t{}\t{}\n"
                .format(timestamp, currency_val["value"], index_val["positive"], 
                    index_val["neutral"], index_val["negative"], index_val["score"]))

        # forecast values
        self.multivar.run(self.store_id, self.streamer.to_safe_timestamp(timestamp))


    def single_run_from_stream(self, n_tweets):
        # download tweets
        tweets, timestamp, filename = self.streamer.stream_tweets(n_tweets=n_tweets)
        print("Tweets saved in file {}.".format(filename))
        self.pipeline(tweets, timestamp)

    def single_run_from_dump(self, timestamp):
        # load tweets
        tweets, timestamp, filename = self.streamer.tweets_from_dump(timestamp)
        print("Tweets from file {}.".format(filename))
        self.pipeline(tweets, timestamp)




if __name__ == '__main__':
    h = Hypeminer("test")
    h.single_run_from_dump("20210318021353")
    # h.single_run_from_stream(n_tweets=10)
