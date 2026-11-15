"""s059: Shock continuation (volatility)

A 12-hour move larger than 3 sigma (of recent bar volatility) is followed in its direction for 2 days.
"""


import numpy as np
import pandas as pd


NAME = 'Shock continuation'
FAMILY = 'volatility'
IDEA = 'A 12-hour move larger than 3 sigma (of recent bar volatility) is followed in its direction for 2 days.'
PARAMS = {'k_bars': 3, 'k': 3.0, 'hold_n': 12, 'vol_n': 180}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def hold(entry, n):
    """Keep the most recent non-zero entry (+1/-1) for n bars."""
    return entry.where(entry != 0).ffill(limit=n - 1).fillna(0)


def signal(df, k_bars, k, hold_n, vol_n):
    c = df["close"]
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    return hold(ls(z > k, z < -k), hold_n)
