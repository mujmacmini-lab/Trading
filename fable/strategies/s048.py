"""s048: Rolling-VWAP band breakout (breakout)

Enter when price closes 2 sigma beyond the 20-day volume-weighted average price; exit back at the VWAP.
"""


import numpy as np
import pandas as pd


NAME = 'Rolling-VWAP band breakout'
FAMILY = 'breakout'
IDEA = 'Enter when price closes 2 sigma beyond the 20-day volume-weighted average price; exit back at the VWAP.'
PARAMS = {'n': 120, 'k': 2.0}


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


def signal(df, n, k):
    c = df["close"]
    tp = (df["high"] + df["low"] + c) / 3
    vwap = (tp * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()
    sd = (c - vwap).rolling(n).std()
    return latch(c > vwap + k * sd, c < vwap, c < vwap - k * sd, c > vwap)
