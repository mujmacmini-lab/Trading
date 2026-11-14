"""s098: Breakout plus momentum plus volume (combination)

40-bar breakout in the direction of 30-day momentum on above-average volume; exit on the 20-bar opposite extreme or a momentum flip.
"""


import numpy as np
import pandas as pd


NAME = 'Breakout plus momentum plus volume'
FAMILY = 'combination'
IDEA = '40-bar breakout in the direction of 30-day momentum on above-average volume; exit on the 20-bar opposite extreme or a momentum flip.'
PARAMS = {'n_in': 40, 'n_out': 20, 'mom_n': 180, 'vol_n': 120, 'vol_mult': 1.2}


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


def signal(df, n_in, n_out, mom_n, vol_n, vol_mult):
    c = df["close"]
    up, dn = c > c.shift(mom_n), c < c.shift(mom_n)
    big = df["volume"] > vol_mult * sma(df["volume"], vol_n).shift(1)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & up & big, (c < xl) | ~up, (c < lo) & dn & big, (c > xh) | ~dn)
