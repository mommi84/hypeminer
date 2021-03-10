#!/bin/bash
val=1612828740000
for i in {0..41}
	do
		curl -s -X GET \
		  "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000&startTime=${val}" \
		  -o "${val}.json"
		((val+=60000000))
		sleep 1
	done
