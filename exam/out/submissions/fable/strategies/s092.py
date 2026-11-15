"""s092: Momentum vote with vol-rank kill switch (combination)

Momentum vote, flat whenever 7-day realised vol is in the top decile of the last 90 days.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum vote with vol-rank kill switch'
FAMILY = 'combination'
IDEA = 'Momentum vote, flat whenever 7-day realised vol is in the top decile of the last 90 days.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'vol_n': 42, 'window': 540, 'cap': 0.9}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, vol_n, window, cap):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    ok = c.pct_change().rolling(vol_n).std().rolling(window).rank(pct=True) < cap
    return ls((v > 0) & ok, (v < 0) & ok)
