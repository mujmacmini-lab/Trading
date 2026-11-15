"""s064: Volatility stop-and-reverse (volatility)

Flip when price closes more than 6 ATR(84) against the best close since the last flip; a side is held only while the 1-4 month momentum vote agrees.
"""


import numpy as np
import pandas as pd


NAME = 'Volatility stop-and-reverse'
FAMILY = 'volatility'
IDEA = 'Flip when price closes more than 6 ATR(84) against the best close since the last flip; a side is held only while the 1-4 month momentum vote agrees.'
PARAMS = {'atr_n': 84, 'mult': 6.0, 'n1': 180, 'n2': 360, 'n3': 540, 'n4': 720}


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


def signal(df, atr_n, mult, n1, n2, n3, n4):
    c = df["close"].to_numpy(dtype=float)
    a = atr(df, atr_n).to_numpy(dtype=float)
    pos = np.zeros(len(c))
    p = 0
    hi = lo = c[0]
    for i in range(1, len(c)):
        hi = max(hi, c[i])
        lo = min(lo, c[i])
        if p <= 0 and c[i] > lo + mult * a[i]:
            p, hi = 1, c[i]
        elif p >= 0 and c[i] < hi - mult * a[i]:
            p, lo = -1, c[i]
        pos[i] = p
    return aligned(pd.Series(pos, index=df.index), mom_vote(df["close"], (n1, n2, n3, n4)))
