"""s029: On-balance volume trend (momentum)

OBV above its 400-bar average long, below short (volume-flow momentum).
"""


import numpy as np
import pandas as pd


NAME = 'On-balance volume trend'
FAMILY = 'momentum'
IDEA = 'OBV above its 400-bar average long, below short (volume-flow momentum).'
PARAMS = {'n': 400}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def obv(df):
    return (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()


def signal(df, n):
    o = obv(df)
    m = sma(o, n)
    return ls(o > m, o < m)
