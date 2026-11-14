"""s024: Smoothed rate of change (momentum)

EMA-smoothed 20-day rate of change: long when positive, short when negative.
"""


import numpy as np
import pandas as pd


NAME = 'Smoothed rate of change'
FAMILY = 'momentum'
IDEA = 'EMA-smoothed 20-day rate of change: long when positive, short when negative.'
PARAMS = {'n': 120, 'smooth': 30}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, smooth):
    roc = ema(df["close"].pct_change(n), smooth)
    return ls(roc > 0, roc < 0)
