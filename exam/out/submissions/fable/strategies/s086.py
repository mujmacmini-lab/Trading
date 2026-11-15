"""s086: Asymmetric-evidence momentum (regime filter)

Long on a simple majority of the 30/60/90-day returns, but short only when all three are negative (shorts need stronger evidence).
"""


import numpy as np
import pandas as pd


NAME = 'Asymmetric-evidence momentum'
FAMILY = 'regime filter'
IDEA = 'Long on a simple majority of the 30/60/90-day returns, but short only when all three are negative (shorts need stronger evidence).'
PARAMS = {'n1': 180, 'n2': 360, 'n3': 540}


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
    spans = (n1, n2, n3)
    v = mom_vote(df["close"], spans)
    return ls(v > 0, v <= -len(spans))
