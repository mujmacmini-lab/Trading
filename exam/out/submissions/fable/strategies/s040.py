"""s040: Closing-high breakout with ATR trail (breakout)

Enter on a 15-day closing high (only above SMA300) or closing low (only below it); exit on a 3.5-ATR trailing stop.
"""


import numpy as np
import pandas as pd


NAME = 'Closing-high breakout with ATR trail'
FAMILY = 'breakout'
IDEA = 'Enter on a 15-day closing high (only above SMA300) or closing low (only below it); exit on a 3.5-ATR trailing stop.'
PARAMS = {'n': 90, 'atr_n': 42, 'mult': 3.5, 'trend_n': 300}


def sma(s, n):
    return s.rolling(n).mean()


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


def signal(df, n, atr_n, mult, trend_n):
    c = df["close"]
    m = sma(c, trend_n)
    return trail((c > c.rolling(n).max().shift(1)) & (c > m), (c < c.rolling(n).min().shift(1)) & (c < m),
                 c, atr(df, atr_n), mult)
