"""s091: Momentum vote with OBV confirmation (combination)

30/60/90-day momentum vote, kept only when on-balance volume is on the same side of its 400-bar average.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum vote with OBV confirmation'
FAMILY = 'combination'
IDEA = '30/60/90-day momentum vote, kept only when on-balance volume is on the same side of its 400-bar average.'
PARAMS = {'n1': 180, 'n2': 360, 'n3': 540, 'obv_n': 400}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def obv(df):
    return (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()


def signal(df, n1, n2, n3, obv_n):
    v = mom_vote(df["close"], (n1, n2, n3))
    o = obv(df)
    m = sma(o, obv_n)
    return ls((v > 0) & (o > m), (v < 0) & (o < m))
