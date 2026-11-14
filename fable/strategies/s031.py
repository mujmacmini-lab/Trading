"""s031: Aroon oscillator (momentum)

Aroon(150): long when the most recent 25-day high is much fresher than the most recent low, short on the mirror.
"""


import numpy as np
import pandas as pd


NAME = 'Aroon oscillator'
FAMILY = 'momentum'
IDEA = 'Aroon(150): long when the most recent 25-day high is much fresher than the most recent low, short on the mirror.'
PARAMS = {'n': 150, 'level': 30}


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


def signal(df, n, level):
    up = df["high"].rolling(n + 1).apply(np.argmax, raw=True) * 100.0 / n
    dn = df["low"].rolling(n + 1).apply(np.argmin, raw=True) * 100.0 / n
    osc = up - dn
    return latch(osc > level, osc < 0, osc < -level, osc > 0)
