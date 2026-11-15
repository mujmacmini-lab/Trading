"""s025: Skip-recent momentum (momentum)

60-day momentum that ignores the latest 5 days (classic skip-period momentum), to avoid short-term reversal noise.
"""


import numpy as np
import pandas as pd


NAME = 'Skip-recent momentum'
FAMILY = 'momentum'
IDEA = '60-day momentum that ignores the latest 5 days (classic skip-period momentum), to avoid short-term reversal noise.'
PARAMS = {'n': 360, 'skip': 30}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, skip):
    c = df["close"]
    ret = c.shift(skip) / c.shift(n) - 1
    return ls(ret > 0, ret < 0)
