"""s070: Volatility-normalised momentum (volatility)

30-day sum of bar returns each divided by the prevailing 7-day volatility, so calm-period moves count as much as wild ones; trade its sign.
"""


import numpy as np
import pandas as pd


NAME = 'Volatility-normalised momentum'
FAMILY = 'volatility'
IDEA = '30-day sum of bar returns each divided by the prevailing 7-day volatility, so calm-period moves count as much as wild ones; trade its sign.'
PARAMS = {'n': 180, 'vol_n': 42}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, vol_n):
    r = df["close"].pct_change()
    s = (r / r.rolling(vol_n).std().shift(1)).rolling(n).sum()
    return ls(s > 0, s < 0)
