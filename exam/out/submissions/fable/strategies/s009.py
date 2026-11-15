"""s009: Donchian midline trend (trend following)

Long when price is in the upper part of its 40-day high-low range, short in the lower part, with a dead zone.
"""


import numpy as np
import pandas as pd


NAME = 'Donchian midline trend'
FAMILY = 'trend following'
IDEA = 'Long when price is in the upper part of its 40-day high-low range, short in the lower part, with a dead zone.'
PARAMS = {'n': 240, 'upper': 0.55, 'lower': 0.45, 'mid': 0.5}


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


def signal(df, n, upper, lower, mid):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    pos = (df["close"] - ll) / (hh - ll)
    return latch(pos > upper, pos < mid, pos < lower, pos > mid)
