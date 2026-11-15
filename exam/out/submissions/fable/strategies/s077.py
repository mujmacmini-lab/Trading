"""s077: Choppiness-index regime (regime filter)

Choppiness index(84) below 50 marks a trending market: follow the 14-day return; flat when choppy.
"""


import numpy as np
import pandas as pd


NAME = 'Choppiness-index regime'
FAMILY = 'regime filter'
IDEA = 'Choppiness index(84) below 50 marks a trending market: follow the 14-day return; flat when choppy.'
PARAMS = {'n': 84, 'level': 50}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n, level):
    c = df["close"]
    pc = c.shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    rng = df["high"].rolling(n).max() - df["low"].rolling(n).min()
    chop = 100 * np.log10(tr.rolling(n).sum() / rng) / np.log10(n)
    ret = c / c.shift(n) - 1
    return ls((chop < level) & (ret > 0), (chop < level) & (ret < 0))
