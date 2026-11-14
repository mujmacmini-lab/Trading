"""s018: Time-series momentum 60d (momentum)

Sign of the 60-day (360-bar) return.
"""


import numpy as np
import pandas as pd


NAME = 'Time-series momentum 60d'
FAMILY = 'momentum'
IDEA = 'Sign of the 60-day (360-bar) return.'
PARAMS = {'n': 360}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n):
    ret = df["close"] / df["close"].shift(n) - 1
    return ls(ret > 0, ret < 0)
