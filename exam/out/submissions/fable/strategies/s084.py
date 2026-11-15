"""s084: Market-structure regime (regime filter)

Higher high and higher low versus the previous 15-day block: long. Lower high and lower low: short. Mixed: flat.
"""


import numpy as np
import pandas as pd


NAME = 'Market-structure regime'
FAMILY = 'regime filter'
IDEA = 'Higher high and higher low versus the previous 15-day block: long. Lower high and lower low: short. Mixed: flat.'
PARAMS = {'n': 90}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    return ls((hh > hh.shift(n)) & (ll > ll.shift(n)), (hh < hh.shift(n)) & (ll < ll.shift(n)))
