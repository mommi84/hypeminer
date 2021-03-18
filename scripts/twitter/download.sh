#!/bin/bash
timestampsfile=$1
# token="AAAAAAAAAAAAAAAAAAAAAOLYNQEAAAAAP%2Bma8Qj1tPhvVj6UdJkCu7%2Bc6BA%3DADAppxvZCyiqgxI9dtwJVRvFedVzFhZVW16mVs5qaI7dbkf8yA"
# envname=dev
token="AAAAAAAAAAAAAAAAAAAAALYMNwEAAAAAjCV%2BmRcDwDNzQg5JCjcVlF%2BujAA%3DoLpq0lFyUWqLlt8EeLjShap77kOVt4UOzlqzq6uC3QT9wlungN"
envname=dev

while read t; do
	echo "${t}"
	curl -s -X POST \
	  https://api.twitter.com/1.1/tweets/search/30day/${envname}.json \
	  -H "Authorization: Bearer ${token}" \
	  -H "Content-Type: application/json" \
	  -d "{
	    \"query\": \"(bitcoin OR btc) lang:en\",
	    \"toDate\": \"${t}\",
	    \"maxResults\": \"100\"
	  }" \
	  -o "${t}.json"
	sleep 2
done < ${timestampsfile}

