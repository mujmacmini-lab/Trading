"""s080: Volume-participation regime (regime filter)

Momentum vote traded only while 7-day average volume is above its 90-day average (moves backed by participation).
"""


import numpy as np
import pandas as pd


NAME = 'Volume-participation regime'
FAMILY = 'regime filter'
IDEA = 'Momentum vote traded only while 7-day average volume is above its 90-day average (moves backed by participation).'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'vol_fast': 42, 'vol_slow': 540}


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


def signal(df, n1, n2, n3, vol_fast, vol_slow):
    v = mom_vote(df["close"], (n1, n2, n3))
    active = sma(df["volume"], vol_fast) > sma(df["volume"], vol_slow)
    return ls((v > 0) & active, (v < 0) & active)
