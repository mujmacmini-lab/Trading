"""s083: Variance-ratio regime (regime filter)

When the 2-day/4-hour variance ratio over 60 days is above 1 (returns trend rather than revert) follow 30-day momentum; else flat.
"""


import numpy as np
import pandas as pd


NAME = 'Variance-ratio regime'
FAMILY = 'regime filter'
IDEA = 'When the 2-day/4-hour variance ratio over 60 days is above 1 (returns trend rather than revert) follow 30-day momentum; else flat.'
PARAMS = {'q': 12, 'window': 360, 'n': 180}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, q, window, n):
    c = df["close"]
    vr = c.pct_change(q).rolling(window).var() / (q * c.pct_change().rolling(window).var())
    ret = c / c.shift(n) - 1
    return ls((vr > 1) & (ret > 0), (vr > 1) & (ret < 0))
