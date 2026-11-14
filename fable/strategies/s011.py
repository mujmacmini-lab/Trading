"""s011: EMA 200 slope and side (trend following)

Long when EMA200 is rising and price is above it, short when falling and price is below, flat when they disagree.
"""


import numpy as np
import pandas as pd


NAME = 'EMA 200 slope and side'
FAMILY = 'trend following'
IDEA = 'Long when EMA200 is rising and price is above it, short when falling and price is below, flat when they disagree.'
PARAMS = {'n': 200, 'slope_n': 30}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, slope_n):
    c = df["close"]
    e = ema(c, n)
    return ls((e > e.shift(slope_n)) & (c > e), (e < e.shift(slope_n)) & (c < e))
