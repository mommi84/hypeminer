#!/usr/bin/env python
import datetime as dt


def output_timestamps(a, b, filename, req_delta=None):
	diff = (b-a).total_seconds()

	if not req_delta:
		tweet_cap = 25000
		tweet_per_req = 100
		req = tweet_cap / tweet_per_req
		req_delta = diff / req
	else:
		req = diff / req_delta

	x = a # a is excluded
	with open(filename, 'w') as f:
	    for i in range(int(req)):
	        x = x + dt.timedelta(seconds=req_delta)
	        ts = x.strftime("%Y%m%d%H%M")
	        print(ts)
	        f.write(ts + '\n')


# a = dt.datetime(2021,2,8,23,59,0)
# b = dt.datetime(2021,3,8,23,59,0)
# filename = 'timestamps.txt'

# output_timestamps(a, b, filename)


a = dt.datetime(2021,3,8,23,59,0)
b = dt.datetime(2021,3,20,23,59,0)
filename = 'timestamps-gap.txt'

output_timestamps(a, b, filename, req_delta=161*60)
