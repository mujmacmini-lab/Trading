"""s027: True Strength Index (momentum)

Double-smoothed momentum (TSI) above/below zero.
"""


import numpy as np
import pandas as pd


NAME = 'True Strength Index'
FAMILY = 'momentum'
IDEA = 'Double-smoothed momentum (TSI) above/below zero.'
PARAMS = {'r': 150, 's': 75}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, r, s):
    d = df["close"].diff()
    tsi = ema(ema(d, r), s) / ema(ema(d.abs(), r), s)
    return ls(tsi > 0, tsi < 0)
