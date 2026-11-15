"""s074: ADX-gated EMA cross (regime filter)

EMA 50/200 direction, traded only while ADX(14) > 20.
"""


import numpy as np
import pandas as pd


NAME = 'ADX-gated EMA cross'
FAMILY = 'regime filter'
IDEA = 'EMA 50/200 direction, traded only while ADX(14) > 20.'
PARAMS = {'fast': 50, 'slow': 200, 'adx_n': 14, 'level': 20}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


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


def signal(df, fast, slow, adx_n, level):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    on = dmi(df, adx_n)[2] > level
    return ls((f > s) & on, (f < s) & on)
