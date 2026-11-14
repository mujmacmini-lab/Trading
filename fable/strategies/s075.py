"""s075: Bull/bear-aligned momentum (regime filter)

30-day momentum, but longs only above the 100-day SMA and shorts only below it.
"""


import numpy as np
import pandas as pd


NAME = 'Bull/bear-aligned momentum'
FAMILY = 'regime filter'
IDEA = '30-day momentum, but longs only above the 100-day SMA and shorts only below it.'
PARAMS = {'n': 180, 'regime_n': 600}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, regime_n):
    c = df["close"]
    ret = c / c.shift(n) - 1
    m = sma(c, regime_n)
    return ls((ret > 0) & (c > m), (ret < 0) & (c < m))
