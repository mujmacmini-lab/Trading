"""s079: Trend-quality (R-squared) regime (regime filter)

Follow the 30-day regression slope only when the fit is clean (R-squared > 0.4); flat in noisy markets.
"""


import numpy as np
import pandas as pd


NAME = 'Trend-quality (R-squared) regime'
FAMILY = 'regime filter'
IDEA = 'Follow the 30-day regression slope only when the fit is clean (R-squared > 0.4); flat in noisy markets.'
PARAMS = {'n': 180, 'r2': 0.4}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, r2):
    y = np.log(df["close"])
    x = pd.Series(np.arange(len(y), dtype=float), index=y.index)
    corr = y.rolling(n).corr(x)
    return ls((corr > 0) & (corr ** 2 > r2), (corr < 0) & (corr ** 2 > r2))
