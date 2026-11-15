"""s052: Pullback-resumption entry (mean reversion)

In a voted uptrend, after at least 6 bars below EMA50 buy the first close back above it and hold until price closes below it again; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Pullback-resumption entry'
FAMILY = 'mean reversion'
IDEA = 'In a voted uptrend, after at least 6 bars below EMA50 buy the first close back above it and hold until price closes below it again; mirrored short.'
PARAMS = {'n': 50, 'k': 6, 'n1': 180, 'n2': 360, 'n3': 540}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n, k, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    e = ema(c, n)
    below, above = c < e, c > e
    was_below = below.shift(1).rolling(k).sum() == k
    was_above = above.shift(1).rolling(k).sum() == k
    up, dn = v > 0, v < 0
    return latch(up & above & was_below, below | ~up, dn & below & was_above, above | ~dn)
