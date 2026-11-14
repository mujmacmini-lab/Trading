"""s076: Efficiency-ratio regime (regime filter)

Kaufman efficiency ratio over 20 days: when the path is efficient (> 0.15) follow its direction, otherwise stay flat.
"""


import numpy as np
import pandas as pd


NAME = 'Efficiency-ratio regime'
FAMILY = 'regime filter'
IDEA = 'Kaufman efficiency ratio over 20 days: when the path is efficient (> 0.15) follow its direction, otherwise stay flat.'
PARAMS = {'n': 120, 'level': 0.15}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, level):
    c = df["close"]
    change = c - c.shift(n)
    er = change.abs() / c.diff().abs().rolling(n).sum()
    return ls((er > level) & (change > 0), (er > level) & (change < 0))
