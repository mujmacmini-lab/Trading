"""s041: Volume-confirmed breakout (breakout)

10-day channel breakout in the direction of the 30/60/90-day momentum vote, on a bar with well-above-average volume; exit on the 5-day opposite extreme.
"""


import numpy as np
import pandas as pd


NAME = 'Volume-confirmed breakout'
FAMILY = 'breakout'
IDEA = '10-day channel breakout in the direction of the 30/60/90-day momentum vote, on a bar with well-above-average volume; exit on the 5-day opposite extreme.'
PARAMS = {'n_in': 60, 'n_out': 30, 'vol_n': 120, 'vol_mult': 1.5, 'n1': 180, 'n2': 360, 'n3': 540}


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def signal(df, n_in, n_out, vol_n, vol_mult, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    big = df["volume"] > vol_mult * sma(df["volume"], vol_n).shift(1)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & big & (v > 0), c < xl, (c < lo) & big & (v < 0), c > xh)
