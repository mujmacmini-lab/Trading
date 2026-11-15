"""s026: Long-window RSI regime (momentum)

RSI(84) as a momentum gauge: long above 55, short below 45, exit on a cross of 50.
"""


import numpy as np
import pandas as pd


NAME = 'Long-window RSI regime'
FAMILY = 'momentum'
IDEA = 'RSI(84) as a momentum gauge: long above 55, short below 45, exit on a cross of 50.'
PARAMS = {'n': 84, 'upper': 55, 'lower': 45, 'mid': 50}


def rsi(s, n):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1.0 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


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
    x = rsi(df["close"], n)
    return latch(x > upper, x < mid, x < lower, x > mid)
