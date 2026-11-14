"""s006: Linear-regression slope (trend following)

Sign of the least-squares slope of log price over 40 days: long when rising, short when falling.
"""


import numpy as np
import pandas as pd


NAME = 'Linear-regression slope'
FAMILY = 'trend following'
IDEA = 'Sign of the least-squares slope of log price over 40 days: long when rising, short when falling.'
PARAMS = {'n': 240}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n):
    y = np.log(df["close"])
    x = pd.Series(np.arange(len(y), dtype=float), index=y.index)
    slope = y.rolling(n).cov(x) / x.rolling(n).var()
    return ls(slope > 0, slope < 0)
