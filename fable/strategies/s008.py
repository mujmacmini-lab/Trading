"""s008: Ichimoku cloud (daily-scaled) (trend following)

Ichimoku scaled x6 to 4h bars: long above the cloud with Tenkan > Kijun, short below with Tenkan < Kijun.
"""


import numpy as np
import pandas as pd


NAME = 'Ichimoku cloud (daily-scaled)'
FAMILY = 'trend following'
IDEA = 'Ichimoku scaled x6 to 4h bars: long above the cloud with Tenkan > Kijun, short below with Tenkan < Kijun.'
PARAMS = {'tenkan': 54, 'kijun': 156, 'span_b': 312}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, tenkan, kijun, span_b):
    h, l, c = df["high"], df["low"], df["close"]
    t = (h.rolling(tenkan).max() + l.rolling(tenkan).min()) / 2
    k = (h.rolling(kijun).max() + l.rolling(kijun).min()) / 2
    sa = ((t + k) / 2).shift(kijun)
    sb = ((h.rolling(span_b).max() + l.rolling(span_b).min()) / 2).shift(kijun)
    top = pd.concat([sa, sb], axis=1).max(axis=1, skipna=False)
    bot = pd.concat([sa, sb], axis=1).min(axis=1, skipna=False)
    return ls((c > top) & (t > k), (c < bot) & (t < k))
