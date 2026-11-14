"""s015: Long-only golden regime (trend following)

Long only while EMA50 > EMA200 and price is above EMA50; flat otherwise (never short).
"""


import numpy as np
import pandas as pd


NAME = 'Long-only golden regime'
FAMILY = 'trend following'
IDEA = 'Long only while EMA50 > EMA200 and price is above EMA50; flat otherwise (never short).'
PARAMS = {'fast': 50, 'slow': 200}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, slow):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    return ls((f > s) & (c > f), pd.Series(False, index=c.index))
