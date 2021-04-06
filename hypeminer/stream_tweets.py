#!/usr/bin/env python
import requests
from datetime import datetime
import json
import os

from hypeminer import utilities


TWEETS_DIR = "data/{}/tweets/"
TWEETS_PATH = TWEETS_DIR + "tweets-{}.json"

STREAMER_URL = "https://api.twitter.com/2/tweets/search/stream?tweet.fields=created_at&expansions=author_id&user.fields=created_at"

STREAMER_HEADERS = {
    'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAAOLYNQEAAAAAP%2Bma8Qj1tPhvVj6UdJkCu7%2Bc6BA%3DADAppxvZCyiqgxI9dtwJVRvFedVzFhZVW16mVs5qaI7dbkf8yA',
    'Content-Type': 'application/json',
}


class TweetStreamer(object):

    """TweetStreamer object."""
    def __init__(self, currency, url=STREAMER_URL, headers=STREAMER_HEADERS):
        self.currency = currency
        self.url = url
        self.headers = headers

    def get_now(self):
        now = datetime.now()
        dt_now = now.strftime("%Y-%m-%d %H:%M:%S")
        safe_dt_now = now.strftime("%Y%m%d%H%M%S")
        return dt_now, safe_dt_now

    def list_file_ids(self):
        file_ids = []
        for file in os.listdir(TWEETS_DIR.format(self.currency)):
            if file.endswith(".json"):
                file_ids.append(file[7:-5])
        return sorted(file_ids)

    def tweets_from_dump(self, safe_timestamp):
        tweets = []
        my_infile = TWEETS_PATH.format(self.currency, safe_timestamp)
        timestamp = utilities.to_timestamp(safe_timestamp)
        with open(my_infile) as f:
            for line in f:
                tweets.append(json.loads(line.strip()))
        return tweets, timestamp, my_infile

    def stream_tweets(self, n_tweets=10):

        timestamp, safe_timestamp = self.get_now()
        my_outfile = TWEETS_PATH.format(self.currency, safe_timestamp)

        s = requests.Session()

        tweets = []
        with s.get(self.url, headers=self.headers, stream=True) as resp, open(my_outfile, 'w') as f_out:
            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    print(line)
                    f_out.write("{}\n".format(line))
                    tweets.append(json.loads(line))
                    if len(tweets) == n_tweets:
                        break

        return tweets, timestamp, my_outfile


if __name__ == '__main__':
    streamer = TweetStreamer("BTCBUSD")
    # tweets, outfile = streamer.stream_tweets(n_tweets=10)
    tweets, outfile = streamer.tweets_from_dump("20210318021353")
    print("Tweets from file {}.".format(outfile))
    print(tweets)
