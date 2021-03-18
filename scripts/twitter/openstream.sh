#!/usr/bin/bash
curl -X GET \  -H 'Authorization: Bearer AAAAAAAAAAAAAAAAAAAAAOLYNQEAAAAAP%2Bma8Qj1tPhvVj6UdJkCu7%2Bc6BA%3DADAppxvZCyiqgxI9dtwJVRvFedVzFhZVW16mVs5qaI7dbkf8yA' \  -H 'Content-Type: application/json' \
  'https://api.twitter.com/2/tweets/search/stream?tweet.fields=created_at&expansions=author_id&user.fields=created_at'
