#!/bin/bash
for i in *.json
	do
		jq '.results[].text' $i >> bitcoin-or-btc-english-v2.txt
	done
