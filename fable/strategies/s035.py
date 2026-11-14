"""s035: Trend-filtered fast Donchian (breakout)

20-bar breakouts taken only in the direction of the 50-day SMA; exit on the opposite 10-bar extreme.
"""


import numpy as np
import pandas as pd


NAME = 'Trend-filtered fast Donchian'
FAMILY = 'breakout'
IDEA = '20-bar breakouts taken only in the direction of the 50-day SMA; exit on the opposite 10-bar extreme.'
PARAMS = {'n_in': 20, 'n_out': 10, 'trend_n': 300}


def sma(s, n):
    return s.rolling(n).mean()


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


def signal(df, n_in, n_out, trend_n):
    c = df["close"]
    m = sma(c, trend_n)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & (c > m), c < xl, (c < lo) & (c < m), c > xh)
