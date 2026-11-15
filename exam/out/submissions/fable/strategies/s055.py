"""s055: EMA-zone pullback (mean reversion)

In an EMA50>EMA200 uptrend buy a dip of 1 ATR below EMA50, exit 1 ATR above it or on trend loss; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'EMA-zone pullback'
FAMILY = 'mean reversion'
IDEA = 'In an EMA50>EMA200 uptrend buy a dip of 1 ATR below EMA50, exit 1 ATR above it or on trend loss; mirrored short.'
PARAMS = {'fast': 50, 'slow': 200, 'atr_n': 42, 'depth': 1.0}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


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


def signal(df, fast, slow, atr_n, depth):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    b = depth * atr(df, atr_n)
    up, dn = f > s, f < s
    return latch(up & (c < f - b), (c > f + b) | ~up, dn & (c > f + b), (c < f - b) | ~dn)
