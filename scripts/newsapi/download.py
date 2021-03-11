#!/usr/bin/env python
import configparser
import json
import time

from newsapi import NewsApiClient

# set owner
owner = 'MARCO'

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config[owner]['api_key']

newsapi = NewsApiClient(api_key=api_key)
published = '2021-03-08T23:59:59Z'

for x in range(0, 100):

    published = published.replace('Z', '')

    everything = newsapi.get_everything(language='en',
                                              page_size=100,
                                              page=1,
                                              q='bitcoin OR btc',
                                              sort_by='publishedAt',
                                              to=published,
                                           )

    published = everything['articles'][-1]['publishedAt']
    print('Getting news for time:', published)

    with open('news.json', 'a') as f:
        json.dump(everything, f, indent=2)
        f.write('\n')

    time.sleep(1)
