"""s069: Expansion-confirmed breakout (volatility)

A 40-bar breakout is taken only if short-term ATR is already above long-term ATR (range expansion); exit on the 20-bar opposite extreme.
"""


import numpy as np
import pandas as pd


NAME = 'Expansion-confirmed breakout'
FAMILY = 'volatility'
IDEA = 'A 40-bar breakout is taken only if short-term ATR is already above long-term ATR (range expansion); exit on the 20-bar opposite extreme.'
PARAMS = {'atr_fast': 12, 'atr_slow': 120, 'ratio': 1.1, 'n_in': 40, 'n_out': 20}


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


def signal(df, atr_fast, atr_slow, ratio, n_in, n_out):
    c = df["close"]
    hot = atr(df, atr_fast) > ratio * atr(df, atr_slow)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & hot, c < xl, (c < lo) & hot, c > xh)
