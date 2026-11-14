"""s063: Uptrend with high-vol kill switch (long-only) (volatility)

Long above SMA300 except when 7-day realised vol is in the top decile of the last 90 days; never short.
"""


import numpy as np
import pandas as pd


NAME = 'Uptrend with high-vol kill switch (long-only)'
FAMILY = 'volatility'
IDEA = 'Long above SMA300 except when 7-day realised vol is in the top decile of the last 90 days; never short.'
PARAMS = {'n': 300, 'vol_n': 42, 'window': 540, 'cap': 0.9}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, vol_n, window, cap):
    c = df["close"]
    rank = c.pct_change().rolling(vol_n).std().rolling(window).rank(pct=True)
    return ls((c > sma(c, n)) & (rank < cap), pd.Series(False, index=c.index))
