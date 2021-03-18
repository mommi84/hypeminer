#!/usr/bin/env python
import json
import os

for file in os.listdir("./tweets"):
    if file.endswith(".json"):
        filename = os.path.join("./tweets", file)
        print(filename)
        with open(filename) as f:
        	data = json.load(f)
        with open(os.path.join("./tweets-out/", "tweets-" + file.replace(".json", "00.json")), 'w') as f_out:
	        for tweet in data['results']:
	        	t = {'id': tweet['id'], 'created_at': tweet['created_at'], 'text': tweet['text']}
	        	f_out.write(json.dumps(t) + '\n')
