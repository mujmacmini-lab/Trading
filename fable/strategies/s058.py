"""s058: Trend-channel lower-half entry (mean reversion)

In a 30-day uptrend buy only when price sits in the lower third of its 5-day range, exit in the upper third; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Trend-channel lower-half entry'
FAMILY = 'mean reversion'
IDEA = 'In a 30-day uptrend buy only when price sits in the lower third of its 5-day range, exit in the upper third; mirrored short.'
PARAMS = {'trend_n': 180, 'n': 30, 'low': 0.33, 'high': 0.67}


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


def signal(df, trend_n, n, low, high):
    c = df["close"]
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    p = (c - ll) / (hh - ll)
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return latch(up & (p < low), (p > high) | ~up, dn & (p > 1 - low), (p < 1 - high) | ~dn)
