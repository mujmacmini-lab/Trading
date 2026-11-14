"""s082: Three-timeframe agreement (regime filter)

Weekly (42-bar) and monthly (180-bar) returns and the 100-day SMA side must all agree; otherwise flat.
"""


import numpy as np
import pandas as pd


NAME = 'Three-timeframe agreement'
FAMILY = 'regime filter'
IDEA = 'Weekly (42-bar) and monthly (180-bar) returns and the 100-day SMA side must all agree; otherwise flat.'
PARAMS = {'fast': 42, 'mid': 180, 'slow': 600}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, mid, slow):
    c = df["close"]
    a = c / c.shift(fast) - 1
    b = c / c.shift(mid) - 1
    m = sma(c, slow)
    return ls((a > 0) & (b > 0) & (c > m), (a < 0) & (b < 0) & (c < m))
