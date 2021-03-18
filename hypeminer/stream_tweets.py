#!/usr/bin/env python
import requests
from datetime import datetime
import json


STREAMER_URL = "https://api.twitter.com/2/tweets/search/stream?tweet.fields=created_at&expansions=author_id&user.fields=created_at"

STREAMER_HEADERS = {
    'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAAOLYNQEAAAAAP%2Bma8Qj1tPhvVj6UdJkCu7%2Bc6BA%3DADAppxvZCyiqgxI9dtwJVRvFedVzFhZVW16mVs5qaI7dbkf8yA',
    'Content-Type': 'application/json',
}


class TweetStreamer(object):

    """TweetStreamer object."""
    def __init__(self, url=STREAMER_URL, headers=STREAMER_HEADERS):
        self.url = url
        self.headers = headers

    def get_now(self):
        now = datetime.now()
        dt_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        safe_dt_now = now.strftime("%Y%m%d%H%M%S")
        return dt_now, safe_dt_now

    def tweets_from_dump(self, timestamp):
        tweets = []
        my_infile = "tweets-{}.json".format(timestamp)
        with open(my_infile) as f:
            for line in f:
                tweets.append(json.loads(line.strip()))
        return tweets, my_infile

    def stream_tweets(self, n_tweets=10):

        _, safe_dt_now = self.get_now()
        my_outfile = "tweets-{}.json".format(safe_dt_now)

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

        return tweets, my_outfile


if __name__ == '__main__':
    streamer = TweetStreamer()
    # tweets, outfile = streamer.stream_tweets(n_tweets=10)
    tweets, outfile = streamer.tweets_from_dump("20210318021353")
    print("Tweets from file {}.".format(outfile))
    print(tweets)
