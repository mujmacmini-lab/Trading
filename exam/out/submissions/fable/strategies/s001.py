"""s001: EMA 50/200 cross (trend following)

Long when EMA50 is above EMA200, short when below (classic slow trend).
"""


import numpy as np
import pandas as pd


NAME = 'EMA 50/200 cross'
FAMILY = 'trend following'
IDEA = 'Long when EMA50 is above EMA200, short when below (classic slow trend).'
PARAMS = {'fast': 50, 'slow': 200}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, slow):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    return ls(f > s, f < s)
