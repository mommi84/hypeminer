#!/usr/bin/env python
import json
import time

from newsapi import NewsApiClient

# marco 4260e1a4caf84d308c6ca7de135c2c2b
# tom 107d897c9a864cccb0d4020b8001ef5c

newsapi = NewsApiClient(api_key='107d897c9a864cccb0d4020b8001ef5c')
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
