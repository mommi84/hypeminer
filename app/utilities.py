#!/usr/bin/env python
import pandas as pd
from datetime import datetime


FEES = 0.0012


def json_to_df(obj):
    d = {k: [] for k in obj[0]}
    for o in obj:
        for k, v in o.items():
            d[k].append(v)
    return pd.DataFrame.from_dict(d)


def to_readable(epoch, millis=True):
    epoch = epoch / 1000 if millis else epoch
    return datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')

