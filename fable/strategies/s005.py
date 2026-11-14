"""s005: Dual SMA side 50d/100d (trend following)

Long only when price is above both the 50-day and 100-day SMAs, short when below both, flat in between.
"""


import numpy as np
import pandas as pd


NAME = 'Dual SMA side 50d/100d'
FAMILY = 'trend following'
IDEA = 'Long only when price is above both the 50-day and 100-day SMAs, short when below both, flat in between.'
PARAMS = {'n1': 300, 'n2': 600}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n1, n2):
    c = df["close"]
    a, b = sma(c, n1), sma(c, n2)
    return ls((c > a) & (c > b), (c < a) & (c < b))
