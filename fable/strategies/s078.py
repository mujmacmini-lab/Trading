"""s078: Regime-sided breakouts (regime filter)

Rising 100-day SMA: only long 10-day breakouts. Falling: only short breakdowns. Exit on the 5-day opposite extreme.
"""


import numpy as np
import pandas as pd


NAME = 'Regime-sided breakouts'
FAMILY = 'regime filter'
IDEA = 'Rising 100-day SMA: only long 10-day breakouts. Falling: only short breakdowns. Exit on the 5-day opposite extreme.'
PARAMS = {'regime_n': 600, 'slope_n': 60, 'n_in': 60, 'n_out': 30}


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


def signal(df, regime_n, slope_n, n_in, n_out):
    c = df["close"]
    m = sma(c, regime_n)
    bull, bear = m > m.shift(slope_n), m < m.shift(slope_n)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & bull, c < xl, (c < lo) & bear, c > xh)
