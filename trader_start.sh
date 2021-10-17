#!/bin/bash
crypto=$1
fiat=$2
export PYTHONPATH=`pwd`
cd dashboard
nohup python3 hyperealtime.py ${crypto} ${fiat} &
cd ../hypetrader
nohup python3 trader.py &
cd ..
