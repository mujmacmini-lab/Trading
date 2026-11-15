"""s085: Extension-capped trend (regime filter)

Momentum vote, but stand aside when price is stretched more than 8 ATR from SMA300 (late, crowded trend).
"""


import numpy as np
import pandas as pd


NAME = 'Extension-capped trend'
FAMILY = 'regime filter'
IDEA = 'Momentum vote, but stand aside when price is stretched more than 8 ATR from SMA300 (late, crowded trend).'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'ma_n': 300, 'atr_n': 42, 'cap': 8.0}


def sma(s, n):
    return s.rolling(n).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, ma_n, atr_n, cap):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    ok = (c - sma(c, ma_n)).abs() < cap * atr(df, atr_n)
    return ls((v > 0) & ok, (v < 0) & ok)
