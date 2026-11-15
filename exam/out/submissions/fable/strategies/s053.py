"""s053: Williams %R pullback in trend (mean reversion)

With price above SMA300, buy when %R(20) drops below -90 and exit above -40 or on trend loss; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Williams %R pullback in trend'
FAMILY = 'mean reversion'
IDEA = 'With price above SMA300, buy when %R(20) drops below -90 and exit above -40 or on trend loss; mirrored short.'
PARAMS = {'trend_n': 300, 'n': 20, 'low': -90, 'exit_level': -40}


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


def signal(df, trend_n, n, low, exit_level):
    c = df["close"]
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    w = -100 * (hh - c) / (hh - ll)
    m = sma(c, trend_n)
    up, dn = c > m, c < m
    return latch(up & (w < low), (w > exit_level) | ~up, dn & (w > -100 - low), (w < -100 - exit_level) | ~dn)
