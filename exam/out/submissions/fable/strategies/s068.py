"""s068: Calm uptrend (long-only) (volatility)

Long only when price is above SMA300 and 7-day realised vol is below its 90-day median (quiet grind higher); never short.
"""


import numpy as np
import pandas as pd


NAME = 'Calm uptrend (long-only)'
FAMILY = 'volatility'
IDEA = 'Long only when price is above SMA300 and 7-day realised vol is below its 90-day median (quiet grind higher); never short.'
PARAMS = {'n': 300, 'vol_n': 42, 'window': 540}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, vol_n, window):
    c = df["close"]
    vol = c.pct_change().rolling(vol_n).std()
    calm = vol < vol.rolling(window).median()
    return ls((c > sma(c, n)) & calm, pd.Series(False, index=c.index))
