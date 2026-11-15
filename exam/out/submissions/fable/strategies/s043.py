"""s043: Previous-week range breakout (breakout)

Close above last calendar week's high (long) or below its low (short), exit at last week's midpoint; kept only with the 30/60/90-day momentum vote.
"""


import numpy as np
import pandas as pd


NAME = 'Previous-week range breakout'
FAMILY = 'breakout'
IDEA = "Close above last calendar week's high (long) or below its low (short), exit at last week's midpoint; kept only with the 30/60/90-day momentum vote."
PARAMS = {'exit_frac': 0.5, 'n1': 180, 'n2': 360, 'n3': 540}


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


def signal(df, exit_frac, n1, n2, n3):
    c = df["close"]
    wid = pd.Series(np.cumsum((df.index.dayofweek == 0) & (df.index.hour == 0)), index=df.index)
    wh = df["high"].groupby(wid).max().shift(1)
    wl = df["low"].groupby(wid).min().shift(1)
    ph, pl = wid.map(wh), wid.map(wl)
    mid = pl + exit_frac * (ph - pl)
    return aligned(latch(c > ph, c < mid, c < pl, c > mid), mom_vote(c, (n1, n2, n3)))
