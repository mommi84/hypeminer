
# coding: utf-8

# In[1]:

#!/usr/bin/env python
import json

indices = [0, 1]

def process_file(filename):
    string_out = ""
    with open(filename) as f:
        data = json.load(f)
        for d in data:
            line = ""
            for i in indices:
                line += str(d[i]) + "\t"
            string_out += "{}\n".format(line.strip())
    return string_out


# In[3]:

import glob, os
with open('../../data/bitcoin-or-btc-en/binance/btcusd.tsv', 'w') as f_out:
    for filename in sorted(glob.glob("../../data/bitcoin-or-btc-en/binance/btcusd/*.json")):
        print(filename)
        string_out = process_file(filename)
        f_out.write(string_out)


# In[ ]:



