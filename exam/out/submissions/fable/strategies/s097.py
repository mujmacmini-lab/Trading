"""s097: Strict confluence (combination)

Momentum vote, SMA300 side and ADX(14) > 15 must all line up; flat otherwise.
"""


import numpy as np
import pandas as pd


NAME = 'Strict confluence'
FAMILY = 'combination'
IDEA = 'Momentum vote, SMA300 side and ADX(14) > 15 must all line up; flat otherwise.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'ma_n': 300, 'adx_n': 14, 'level': 15}


def sma(s, n):
    return s.rolling(n).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def dmi(df, n):
    """Wilder +DI, -DI and ADX."""
    up = df["high"].diff()
    dn = -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    a = atr(df, n)
    pdi = 100 * pdm.ewm(alpha=1.0 / n, adjust=False).mean() / a
    mdi = 100 * mdm.ewm(alpha=1.0 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return pdi, mdi, dx.ewm(alpha=1.0 / n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, ma_n, adx_n, level):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    m = sma(c, ma_n)
    on = dmi(df, adx_n)[2] > level
    return ls((v > 0) & (c > m) & on, (v < 0) & (c < m) & on)
