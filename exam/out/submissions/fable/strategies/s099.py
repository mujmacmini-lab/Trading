"""s099: Slow EMA with fast Keltner agreement (combination)

Position only when the EMA 50/200 direction and the fast Keltner 20/2 breakout state point the same way.
"""


import numpy as np
import pandas as pd


NAME = 'Slow EMA with fast Keltner agreement'
FAMILY = 'combination'
IDEA = 'Position only when the EMA 50/200 direction and the fast Keltner 20/2 breakout state point the same way.'
PARAMS = {'fast': 50, 'slow': 200, 'kel_n': 20, 'kel_k': 2.0}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


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


def keltner(df, n, k):
    """ATR-channel breakout state: enter beyond EMA +/- k*ATR, exit back at the EMA."""
    c = df["close"]
    m = ema(c, n)
    a = atr(df, n)
    return latch(c > m + k * a, c < m, c < m - k * a, c > m)


def signal(df, fast, slow, kel_n, kel_k):
    c = df["close"]
    d = np.sign(ema(c, fast) - ema(c, slow))
    state = keltner(df, kel_n, kel_k)
    return ls((d > 0) & (state > 0), (d < 0) & (state < 0))
