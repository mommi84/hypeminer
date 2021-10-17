#!/bin/bash
export PYTHONPATH=`pwd`
cd hypetrader
nohup python3 ocotrader.py &
cd ..
