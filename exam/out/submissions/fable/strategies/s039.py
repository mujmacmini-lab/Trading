"""s039: Bollinger breakout with 60d momentum (breakout)

Close outside the 2-sigma band of SMA100 (strength, not reversal), held to the SMA, kept only when it agrees with the 60-day return.
"""


import numpy as np
import pandas as pd


NAME = 'Bollinger breakout with 60d momentum'
FAMILY = 'breakout'
IDEA = 'Close outside the 2-sigma band of SMA100 (strength, not reversal), held to the SMA, kept only when it agrees with the 60-day return.'
PARAMS = {'n': 100, 'k': 2.0, 'mom_n': 360}


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


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


def signal(df, n, k, mom_n):
    c = df["close"]
    m = sma(c, n)
    sd = c.rolling(n).std()
    state = latch(c > m + k * sd, c < m, c < m - k * sd, c > m)
    return aligned(state, c / c.shift(mom_n) - 1)
