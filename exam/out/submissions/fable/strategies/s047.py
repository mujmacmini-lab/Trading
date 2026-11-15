"""s047: Daily-close 30d/15d breakout (breakout)

Turtle-style rule on daily closes only (the 20:00 UTC bar): enter on a 30-day closing high/low, exit on the 15-day opposite.
"""


import numpy as np
import pandas as pd


NAME = 'Daily-close 30d/15d breakout'
FAMILY = 'breakout'
IDEA = 'Turtle-style rule on daily closes only (the 20:00 UTC bar): enter on a 30-day closing high/low, exit on the 15-day opposite.'
PARAMS = {'n_in': 30, 'n_out': 15, 'close_hour': 20}


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


def signal(df, n_in, n_out, close_hour):
    d = df["close"][df.index.hour == close_hour]
    hi = d.rolling(n_in).max().shift(1)
    lo = d.rolling(n_in).min().shift(1)
    xh = d.rolling(n_out).max().shift(1)
    xl = d.rolling(n_out).min().shift(1)
    return latch(d > hi, d < xl, d < lo, d > xh).reindex(df.index).ffill().fillna(0)
