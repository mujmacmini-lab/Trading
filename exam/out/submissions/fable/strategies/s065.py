"""s065: Expanding-bandwidth trend (volatility)

Trade the side of SMA60 only while band width is above its 20-day average (volatility expanding) and the 60-day return agrees; else flat.
"""


import numpy as np
import pandas as pd


NAME = 'Expanding-bandwidth trend'
FAMILY = 'volatility'
IDEA = 'Trade the side of SMA60 only while band width is above its 20-day average (volatility expanding) and the 60-day return agrees; else flat.'
PARAMS = {'n': 60, 'avg_n': 120, 'mom_n': 360}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


def signal(df, n, avg_n, mom_n):
    c = df["close"]
    m = sma(c, n)
    width = c.rolling(n).std() / m
    expanding = width > sma(width, avg_n)
    return aligned(ls((c > m) & expanding, (c < m) & expanding), c / c.shift(mom_n) - 1)
