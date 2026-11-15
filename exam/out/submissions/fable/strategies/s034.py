"""s034: Donchian 40/20 bars (breakout)

Faster channel: enter on a 40-bar breakout, exit on the opposite 20-bar extreme.
"""


import numpy as np
import pandas as pd


NAME = 'Donchian 40/20 bars'
FAMILY = 'breakout'
IDEA = 'Faster channel: enter on a 40-bar breakout, exit on the opposite 20-bar extreme.'
PARAMS = {'n_in': 40, 'n_out': 20}


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


def donchian(df, n_in, n_out):
    """Channel breakout state: enter on a close beyond the prior n_in-bar extreme, exit on the prior n_out-bar opposite extreme."""
    c = df["close"]
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch(c > hi, c < xl, c < lo, c > xh)


def signal(df, n_in, n_out):
    return donchian(df, n_in, n_out)
