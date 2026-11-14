"""s056: Bull-regime deep dip (long-only) (mean reversion)

Above the 100-day SMA, buy a close 2 sigma below SMA50 and exit back at SMA50; never short.
"""


import numpy as np
import pandas as pd


NAME = 'Bull-regime deep dip (long-only)'
FAMILY = 'mean reversion'
IDEA = 'Above the 100-day SMA, buy a close 2 sigma below SMA50 and exit back at SMA50; never short.'
PARAMS = {'regime_n': 600, 'n': 50, 'k': 2.0}


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


def signal(df, regime_n, n, k):
    c = df["close"]
    z = (c - sma(c, n)) / c.rolling(n).std()
    none = pd.Series(False, index=c.index)
    return latch((c > sma(c, regime_n)) & (z < -k), z > 0, none, none)
