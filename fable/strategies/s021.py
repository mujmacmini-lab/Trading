"""s021: Vol-scaled momentum with threshold (momentum)

30-day return in units of its own volatility: enter beyond +/-0.5 sigma, exit when it crosses zero.
"""


import numpy as np
import pandas as pd


NAME = 'Vol-scaled momentum with threshold'
FAMILY = 'momentum'
IDEA = '30-day return in units of its own volatility: enter beyond +/-0.5 sigma, exit when it crosses zero.'
PARAMS = {'n': 180, 'enter': 0.5}


def latch(long_in, long_out, short_in, short_out):
    """Stateful position: enter on *_in, hold until *_out. Exits are processed before entries."""
    idx = long_in.index
    li, lo, si, so = (np.asarray(x, dtype=bool) for x in (long_in, long_out, short_in, short_out))
    pos = np.zeros(len(li))
    p = 0
    for i in range(len(li)):
        if p == 1 and lo[i]:
            p = 0
        elif p == -1 and so[i]:
            p = 0
        if p == 0:
            if li[i] and not lo[i]:
                p = 1
            elif si[i] and not so[i]:
                p = -1
        pos[i] = p
    return pd.Series(pos, index=idx)


def signal(df, n, enter):
    c = df["close"]
    z = (c / c.shift(n) - 1) / (c.pct_change().rolling(n).std() * n ** 0.5)
    return latch(z > enter, z < 0, z < -enter, z > 0)
