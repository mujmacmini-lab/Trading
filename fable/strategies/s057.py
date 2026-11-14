"""s057: VWAP pullback in voted trend (mean reversion)

With the momentum vote up, buy when price closes 1 ATR below the 7-day rolling VWAP and exit back at the VWAP or on a vote flip; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'VWAP pullback in voted trend'
FAMILY = 'mean reversion'
IDEA = 'With the momentum vote up, buy when price closes 1 ATR below the 7-day rolling VWAP and exit back at the VWAP or on a vote flip; mirrored short.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'vwap_n': 42, 'atr_n': 42, 'depth': 1.0}


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, vwap_n, atr_n, depth):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    tp = (df["high"] + df["low"] + c) / 3
    vwap = (tp * df["volume"]).rolling(vwap_n).sum() / df["volume"].rolling(vwap_n).sum()
    b = depth * atr(df, atr_n)
    up, dn = v > 0, v < 0
    return latch(up & (c < vwap - b), (c > vwap) | ~up, dn & (c > vwap + b), (c < vwap) | ~dn)
