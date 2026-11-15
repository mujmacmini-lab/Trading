"""s072: Volatility-regime speed switch (volatility)

Use a slow 30d/15d channel when realised vol is above its 90-day norm and a fast 40/20-bar channel when it is below.
"""


import numpy as np
import pandas as pd


NAME = 'Volatility-regime speed switch'
FAMILY = 'volatility'
IDEA = 'Use a slow 30d/15d channel when realised vol is above its 90-day norm and a fast 40/20-bar channel when it is below.'
PARAMS = {'vol_fast': 42, 'vol_slow': 540, 'slow_in': 180, 'slow_out': 90, 'fast_in': 40, 'fast_out': 20}


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


def signal(df, vol_fast, vol_slow, slow_in, slow_out, fast_in, fast_out):
    r = df["close"].pct_change()
    high_vol = r.rolling(vol_fast).std() > r.rolling(vol_slow).std()
    slow = donchian(df, slow_in, slow_out)
    fast = donchian(df, fast_in, fast_out)
    return slow.where(high_vol, fast)
