"""s096: Pullback entry with trailing exit (combination)

In a voted uptrend buy an RSI(14) < 45 dip and ride it with a 4-ATR trailing stop; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Pullback entry with trailing exit'
FAMILY = 'combination'
IDEA = 'In a voted uptrend buy an RSI(14) < 45 dip and ride it with a 4-ATR trailing stop; mirrored short.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'rsi_n': 14, 'low': 45, 'atr_n': 42, 'mult': 4.0}


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def rsi(s, n):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1.0 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, rsi_n, low, atr_n, mult):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    x = rsi(c, rsi_n)
    return trail((v > 0) & (x < low), (v < 0) & (x > 100 - low), c, atr(df, atr_n), mult)
