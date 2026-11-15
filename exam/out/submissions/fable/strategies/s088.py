"""s088: Trend with pullback-or-breakout entries (combination)

In a voted uptrend enter on either an RSI(4) dip or a 40-bar breakout; exit on a 40-bar low or trend flip; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Trend with pullback-or-breakout entries'
FAMILY = 'combination'
IDEA = 'In a voted uptrend enter on either an RSI(4) dip or a 40-bar breakout; exit on a 40-bar low or trend flip; mirrored short.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'rsi_n': 4, 'low': 25, 'n_brk': 40}


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, rsi_n, low, n_brk):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    x = rsi(c, rsi_n)
    hi = df["high"].rolling(n_brk).max().shift(1)
    lo = df["low"].rolling(n_brk).min().shift(1)
    up, dn = v > 0, v < 0
    return latch(up & ((x < low) | (c > hi)), (c < lo) | ~up, dn & ((x > 100 - low) | (c < lo)), (c > hi) | ~dn)
