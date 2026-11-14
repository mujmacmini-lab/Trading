"""s060: Momentum vote with volatility ceiling (volatility)

Momentum vote (15/30/60d) traded only while 7-day realised vol is below 1.5x its 90-day level; flat in vol spikes.
"""


import numpy as np
import pandas as pd


NAME = 'Momentum vote with volatility ceiling'
FAMILY = 'volatility'
IDEA = 'Momentum vote (15/30/60d) traded only while 7-day realised vol is below 1.5x its 90-day level; flat in vol spikes.'
PARAMS = {'n1': 90, 'n2': 180, 'n3': 360, 'vol_fast': 42, 'vol_slow': 540, 'ceiling': 1.5}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n1, n2, n3, vol_fast, vol_slow, ceiling):
    c = df["close"]
    r = c.pct_change()
    v = mom_vote(c, (n1, n2, n3))
    calm = r.rolling(vol_fast).std() < ceiling * r.rolling(vol_slow).std()
    return ls((v > 0) & calm, (v < 0) & calm)
