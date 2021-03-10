#!/bin/bash
while read t; do
	echo "${t}"
	curl -s -X POST \
	  https://api.twitter.com/1.1/tweets/search/30day/dev.json \
	  -H 'Authorization: Bearer AAAAAAAAAAAAAAAAAAAAAOLYNQEAAAAAP%2Bma8Qj1tPhvVj6UdJkCu7%2Bc6BA%3DADAppxvZCyiqgxI9dtwJVRvFedVzFhZVW16mVs5qaI7dbkf8yA' \
	  -H 'Content-Type: application/json' \
	  -d "{
	    \"query\": \"(bitcoin OR btc) lang:en\",
	    \"toDate\": \"${t}\",
	    \"maxResults\": \"100\"
	  }" \
	  -o "${t}.json"
	sleep 2
done < timestamps.txt
