"""s066: Up/down semivariance ratio (volatility)

Compare 30-day upside and downside realised variance: long when upside dominates, short when downside dominates.
"""


import numpy as np
import pandas as pd


NAME = 'Up/down semivariance ratio'
FAMILY = 'volatility'
IDEA = 'Compare 30-day upside and downside realised variance: long when upside dominates, short when downside dominates.'
PARAMS = {'n': 180, 'ratio': 1.2}


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


def signal(df, n, ratio):
    r = df["close"].pct_change()
    up = (r.clip(lower=0) ** 2).rolling(n).sum()
    dn = (r.clip(upper=0) ** 2).rolling(n).sum()
    q = up / dn
    return latch(q > ratio, q < 1, q < 1 / ratio, q > 1)
