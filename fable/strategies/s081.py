"""s081: Autocorrelation regime (regime filter)

Trade the momentum vote only while daily returns are positively autocorrelated over the last 60 days (trending regime).
"""


import numpy as np
import pandas as pd


NAME = 'Autocorrelation regime'
FAMILY = 'regime filter'
IDEA = 'Trade the momentum vote only while daily returns are positively autocorrelated over the last 60 days (trending regime).'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'lag': 6, 'window': 360}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, lag, window):
    c = df["close"]
    r = c.pct_change(lag)
    ac = r.rolling(window).corr(r.shift(lag))
    v = mom_vote(c, (n1, n2, n3))
    return ls((v > 0) & (ac > 0), (v < 0) & (ac > 0))
