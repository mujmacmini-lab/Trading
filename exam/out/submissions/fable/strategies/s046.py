"""s046: Swing-pivot breakout (breakout)

Close above the last confirmed swing high (pivot with ~3 days each side) is long, below the last swing low is short; kept only with the 60-day return.
"""


import numpy as np
import pandas as pd


NAME = 'Swing-pivot breakout'
FAMILY = 'breakout'
IDEA = 'Close above the last confirmed swing high (pivot with ~3 days each side) is long, below the last swing low is short; kept only with the 60-day return.'
PARAMS = {'k': 20, 'mom_n': 360}


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


def signal(df, k, mom_n):
    h, l, c = df["high"], df["low"], df["close"]
    w = 2 * k + 1
    ph = h.shift(k).where(h.shift(k) == h.rolling(w).max()).ffill()
    pl = l.shift(k).where(l.shift(k) == l.rolling(w).min()).ffill()
    return aligned(latch(c > ph, c < pl, c < pl, c > ph), c / c.shift(mom_n) - 1)
