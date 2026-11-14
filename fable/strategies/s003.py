"""s003: SMA 300 with ATR hysteresis (trend following)

Long once price closes an ATR band above the 50-day SMA, out when it closes back below the SMA; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'SMA 300 with ATR hysteresis'
FAMILY = 'trend following'
IDEA = 'Long once price closes an ATR band above the 50-day SMA, out when it closes back below the SMA; mirrored short.'
PARAMS = {'n': 300, 'atr_n': 42, 'band': 1.0}


def sma(s, n):
    return s.rolling(n).mean()


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


def signal(df, n, atr_n, band):
    c = df["close"]
    m = sma(c, n)
    b = band * atr(df, atr_n)
    return latch(c > m + b, c < m, c < m - b, c > m)
