"""s093: Six-horizon momentum score with hysteresis (combination)

Net count of six return horizons (10 to 80 days): enter at a 4-to-2 majority, hold until the score crosses zero.
"""


import numpy as np
import pandas as pd


NAME = 'Six-horizon momentum score with hysteresis'
FAMILY = 'combination'
IDEA = 'Net count of six return horizons (10 to 80 days): enter at a 4-to-2 majority, hold until the score crosses zero.'
PARAMS = {'n1': 60, 'n2': 120, 'n3': 180, 'n4': 240, 'n5': 360, 'n6': 480, 'enter': 2}


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


def signal(df, n1, n2, n3, n4, n5, n6, enter):
    c = df["close"]
    spans = (n1, n2, n3, n4, n5, n6)
    v = mom_vote(c, spans).where(c.shift(max(spans)).notna())
    return latch(v >= enter, v <= 0, v <= -enter, v >= 0)
