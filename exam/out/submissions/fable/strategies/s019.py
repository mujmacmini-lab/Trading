"""s019: Momentum majority vote 15/30/60d (momentum)

Majority vote of the signs of the 15-, 30- and 60-day returns.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum majority vote 15/30/60d'
FAMILY = 'momentum'
IDEA = 'Majority vote of the signs of the 15-, 30- and 60-day returns.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3):
    v = mom_vote(df["close"], (n1, n2, n3))
    ready = df["close"].shift(max(n1, n2, n3)).notna()
    return ls((v > 0) & ready, (v < 0) & ready)
