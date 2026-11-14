"""s002: EMA 30/120 cross with ATR buffer (trend following)

EMA cross that only flips once the EMA gap exceeds a fraction of ATR, to skip whipsaw crosses.
"""


import numpy as np
import pandas as pd


NAME = 'EMA 30/120 cross with ATR buffer'
FAMILY = 'trend following'
IDEA = 'EMA cross that only flips once the EMA gap exceeds a fraction of ATR, to skip whipsaw crosses.'
PARAMS = {'fast': 30, 'slow': 120, 'atr_n': 42, 'buffer': 0.5}


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


def signal(df, fast, slow, atr_n, buffer):
    c = df["close"]
    gap = ema(c, fast) - ema(c, slow)
    band = buffer * atr(df, atr_n)
    return latch(gap > band, gap < 0, gap < -band, gap > 0)
