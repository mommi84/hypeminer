#!/bin/bash
for i in *.json
	do 
		jq -r '.[][1]' ${i} >> btcusd.txt
	done
