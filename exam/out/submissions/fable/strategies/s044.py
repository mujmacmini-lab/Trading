"""s044: Previous-month range breakout (breakout)

Long on a close above last calendar month's high, short below its low; exit at last month's midpoint.
"""


import numpy as np
import pandas as pd


NAME = 'Previous-month range breakout'
FAMILY = 'breakout'
IDEA = "Long on a close above last calendar month's high, short below its low; exit at last month's midpoint."
PARAMS = {'exit_frac': 0.5}


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


def signal(df, exit_frac):
    c = df["close"]
    mid_ = pd.Series(np.cumsum((df.index.day == 1) & (df.index.hour == 0)), index=df.index)
    ph = mid_.map(df["high"].groupby(mid_).max().shift(1))
    pl = mid_.map(df["low"].groupby(mid_).min().shift(1))
    mid = pl + exit_frac * (ph - pl)
    return latch(c > ph, c < mid, c < pl, c > mid)
