#!/usr/bin/env python
import json
import os
import sys

PART = int(sys.argv[1])

for file in os.listdir(f"./tweets/tweets-part{PART}-in"):
    if file.endswith(".json"):
        filename = os.path.join(f"./tweets/tweets-part{PART}-in", file)
        print(filename)
        with open(filename) as f:
        	data = json.load(f)
        with open(f"./tweets/tweets-part{PART}-out/tweets-{file.replace('.json', '00.json')}", 'w') as f_out:
	        for tweet in data['results']:
	        	t = {'id': tweet['id'], 'created_at': tweet['created_at'], 'text': tweet['text']}
	        	f_out.write(json.dumps(t) + '\n')
