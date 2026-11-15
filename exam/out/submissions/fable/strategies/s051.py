"""s051: Bollinger pullback in trend (mean reversion)

In a 30-day uptrend buy a close 1.5 sigma below SMA30, exit at the SMA; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Bollinger pullback in trend'
FAMILY = 'mean reversion'
IDEA = 'In a 30-day uptrend buy a close 1.5 sigma below SMA30, exit at the SMA; mirrored short.'
PARAMS = {'trend_n': 180, 'n': 30, 'k': 1.5}


def sma(s, n):
    return s.rolling(n).mean()


def latch(long_in, long_out, short_in, short_out):
    """Stateful position: enter on *_in, hold until *_out. Exits are processed before entries."""
    idx = long_in.index
    li, lo, si, so = (np.asarray(x, dtype=bool) for x in (long_in, long_out, short_in, short_out))
    pos = np.zeros(len(li))
    p = 0
    for i in range(len(li)):
        if p == 1 and lo[i]:
            p = 0
        elif p == -1 and so[i]:
            p = 0
        if p == 0:
            if li[i] and not lo[i]:
                p = 1
            elif si[i] and not so[i]:
                p = -1
        pos[i] = p
    return pd.Series(pos, index=idx)


def signal(df, trend_n, n, k):
    c = df["close"]
    z = (c - sma(c, n)) / c.rolling(n).std()
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return latch(up & (z < -k), (z > 0) | ~up, dn & (z > k), (z < 0) | ~dn)
