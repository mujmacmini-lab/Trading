"""s042: Keltner 20/2 in voted trend (breakout)

Fast ATR-channel breakouts (2 ATR beyond EMA20, exit at the EMA) taken only in the direction of the 30/60/90-day momentum vote.
"""


import numpy as np
import pandas as pd


NAME = 'Keltner 20/2 in voted trend'
FAMILY = 'breakout'
IDEA = 'Fast ATR-channel breakouts (2 ATR beyond EMA20, exit at the EMA) taken only in the direction of the 30/60/90-day momentum vote.'
PARAMS = {'n': 20, 'k': 2.0, 'n1': 180, 'n2': 360, 'n3': 540}


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n, k, n1, n2, n3):
    state = keltner(df, n, k)
    v = mom_vote(df["close"], (n1, n2, n3))
    return ls((state > 0) & (v > 0), (state < 0) & (v < 0))
