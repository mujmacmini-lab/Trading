"""s013: Chandelier trend (trend following)

Enter on a 20-day closing high/low, exit on a 4-ATR trailing stop from the best close since entry.
"""


import numpy as np
import pandas as pd


NAME = 'Chandelier trend'
FAMILY = 'trend following'
IDEA = 'Enter on a 20-day closing high/low, exit on a 4-ATR trailing stop from the best close since entry.'
PARAMS = {'n': 120, 'atr_n': 42, 'mult': 4.0}


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def trail(long_in, short_in, close, a, mult):
    """Enter on *_in, exit on an ATR trailing stop measured from the best close since entry."""
    li = np.asarray(long_in, dtype=bool)
    si = np.asarray(short_in, dtype=bool)
    c = close.to_numpy(dtype=float)
    av = a.to_numpy(dtype=float)
    pos = np.zeros(len(c))
    p = 0
    ext = 0.0
    for i in range(len(c)):
        if p == 1:
            ext = max(ext, c[i])
            if c[i] < ext - mult * av[i]:
                p = 0
        elif p == -1:
            ext = min(ext, c[i])
            if c[i] > ext + mult * av[i]:
                p = 0
        if p == 0:
            if li[i]:
                p, ext = 1, c[i]
            elif si[i]:
                p, ext = -1, c[i]
        pos[i] = p
    return pd.Series(pos, index=close.index)


def signal(df, n, atr_n, mult):
    c = df["close"]
    hi = c.rolling(n).max().shift(1)
    lo = c.rolling(n).min().shift(1)
    return trail(c > hi, c < lo, c, atr(df, atr_n), mult)
