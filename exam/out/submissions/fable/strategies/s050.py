"""s050: Stop-run reclaim in slow trend (mean reversion)

With the 30/60/90-day vote up, a bar that undercuts the prior 5-day low but closes back above it is bought for 4 days; mirrored short.
"""


import numpy as np
import pandas as pd


NAME = 'Stop-run reclaim in slow trend'
FAMILY = 'mean reversion'
IDEA = 'With the 30/60/90-day vote up, a bar that undercuts the prior 5-day low but closes back above it is bought for 4 days; mirrored short.'
PARAMS = {'n': 30, 'hold_n': 24, 'n1': 180, 'n2': 360, 'n3': 540}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def hold(entry, n):
    """Keep the most recent non-zero entry (+1/-1) for n bars."""
    return entry.where(entry != 0).ffill(limit=n - 1).fillna(0)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n, hold_n, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    pl = df["low"].rolling(n).min().shift(1)
    ph = df["high"].rolling(n).max().shift(1)
    e = ls((df["low"] < pl) & (c > pl) & (v > 0), (df["high"] > ph) & (c < ph) & (v < 0))
    return hold(e, hold_n)
