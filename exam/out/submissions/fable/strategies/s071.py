"""s071: Trend-aligned shock (volatility)

A 1-day move beyond 2.5 sigma is followed for 3 days, but only when it agrees with the 30-day trend.
"""


import numpy as np
import pandas as pd


NAME = 'Trend-aligned shock'
FAMILY = 'volatility'
IDEA = 'A 1-day move beyond 2.5 sigma is followed for 3 days, but only when it agrees with the 30-day trend.'
PARAMS = {'k_bars': 6, 'k': 2.5, 'hold_n': 18, 'vol_n': 180, 'trend_n': 180}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def hold(entry, n):
    """Keep the most recent non-zero entry (+1/-1) for n bars."""
    return entry.where(entry != 0).ffill(limit=n - 1).fillna(0)


def signal(df, k_bars, k, hold_n, vol_n, trend_n):
    c = df["close"]
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return hold(ls((z > k) & up, (z < -k) & dn), hold_n)
