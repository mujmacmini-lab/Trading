"""s061: Bollinger squeeze breakout (volatility)

After band width falls into the bottom quartile of the last 40 days, trade the next 40-bar breakout in the direction of the momentum vote; exit at the SMA.
"""


import numpy as np
import pandas as pd


NAME = 'Bollinger squeeze breakout'
FAMILY = 'volatility'
IDEA = 'After band width falls into the bottom quartile of the last 40 days, trade the next 40-bar breakout in the direction of the momentum vote; exit at the SMA.'
PARAMS = {'n': 40, 'window': 240, 'q': 0.25, 'recent': 6, 'n1': 180, 'n2': 360, 'n3': 540}


def sma(s, n):
    return s.rolling(n).mean()


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


def signal(df, n, window, q, recent, n1, n2, n3):
    c = df["close"]
    m = sma(c, n)
    width = c.rolling(n).std() / m
    squeezed = width.rolling(window).rank(pct=True).rolling(recent).min() < q
    hi = df["high"].rolling(n).max().shift(1)
    lo = df["low"].rolling(n).min().shift(1)
    v = mom_vote(c, (n1, n2, n3))
    return latch((c > hi) & squeezed & (v > 0), c < m, (c < lo) & squeezed & (v < 0), c > m)
