"""s004: Triple EMA alignment (trend following)

Long only when EMA20 > EMA60 > EMA180 (all horizons aligned), short when fully inverted, otherwise flat.
"""


import numpy as np
import pandas as pd


NAME = 'Triple EMA alignment'
FAMILY = 'trend following'
IDEA = 'Long only when EMA20 > EMA60 > EMA180 (all horizons aligned), short when fully inverted, otherwise flat.'
PARAMS = {'fast': 20, 'mid': 60, 'slow': 180}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, mid, slow):
    c = df["close"]
    a, b, d = ema(c, fast), ema(c, mid), ema(c, slow)
    return ls((a > b) & (b > d), (a < b) & (b < d))
