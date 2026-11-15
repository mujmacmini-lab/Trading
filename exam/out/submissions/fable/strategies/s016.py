"""s016: Two-speed EMA consensus (trend following)

Trade only when a fast (20/100) and a slow (50/200) EMA system agree; flat when they disagree.
"""


import numpy as np
import pandas as pd


NAME = 'Two-speed EMA consensus'
FAMILY = 'trend following'
IDEA = 'Trade only when a fast (20/100) and a slow (50/200) EMA system agree; flat when they disagree.'
PARAMS = {'f1': 20, 's1': 100, 'f2': 50, 's2': 200}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, f1, s1, f2, s2):
    c = df["close"]
    a = np.sign(ema(c, f1) - ema(c, s1))
    b = np.sign(ema(c, f2) - ema(c, s2))
    return ls((a > 0) & (b > 0), (a < 0) & (b < 0))
