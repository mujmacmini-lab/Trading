"""s094: Momentum vote with adverse-shock pause (combination)

Momentum vote, but step aside for 2 days after a 12-hour move of more than 3 sigma against the position.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum vote with adverse-shock pause'
FAMILY = 'combination'
IDEA = 'Momentum vote, but step aside for 2 days after a 12-hour move of more than 3 sigma against the position.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'k_bars': 3, 'k': 3.0, 'pause': 12, 'vol_n': 180}


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, k_bars, k, pause, vol_n):
    c = df["close"]
    v = np.sign(mom_vote(c, (n1, n2, n3))).where(c.shift(max(n1, n2, n3)).notna(), 0)
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    adverse = ((v > 0) & (z < -k)) | ((v < 0) & (z > k))
    paused = adverse.astype(float).rolling(pause).max() > 0
    return v.where(~paused, 0)
