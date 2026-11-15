"""s028: Volume-weighted momentum (momentum)

Sign of the volume-weighted average bar return over 30 days (moves on heavy volume count more).
"""


import numpy as np
import pandas as pd


NAME = 'Volume-weighted momentum'
FAMILY = 'momentum'
IDEA = 'Sign of the volume-weighted average bar return over 30 days (moves on heavy volume count more).'
PARAMS = {'n': 180}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n):
    r = df["close"].pct_change()
    vw = (r * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()
    return ls(vw > 0, vw < 0)
