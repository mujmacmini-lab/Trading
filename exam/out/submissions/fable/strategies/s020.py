"""s020: Momentum vote 30/60/90/120d (momentum)

Signs of the 1-, 2-, 3- and 4-month returns vote: long on a majority up, short on a majority down, flat on a 2-2 tie.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum vote 30/60/90/120d'
FAMILY = 'momentum'
IDEA = 'Signs of the 1-, 2-, 3- and 4-month returns vote: long on a majority up, short on a majority down, flat on a 2-2 tie.'
PARAMS = {'n1': 180, 'n2': 360, 'n3': 540, 'n4': 720}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, n4):
    v = mom_vote(df["close"], (n1, n2, n3, n4))
    return ls(v > 0, v < 0)
