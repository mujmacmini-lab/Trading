"""s032: Range-position momentum (momentum)

Smoothed position of price inside its 50-day range (slow stochastic): long above 60%, short below 40%, exit at 50%.
"""


import numpy as np
import pandas as pd


NAME = 'Range-position momentum'
FAMILY = 'momentum'
IDEA = 'Smoothed position of price inside its 50-day range (slow stochastic): long above 60%, short below 40%, exit at 50%.'
PARAMS = {'n': 300, 'smooth': 6, 'upper': 0.6, 'lower': 0.4, 'mid': 0.5}


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


def signal(df, n, smooth, upper, lower, mid):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    k = sma((df["close"] - ll) / (hh - ll), smooth)
    return latch(k > upper, k < mid, k < lower, k > mid)
