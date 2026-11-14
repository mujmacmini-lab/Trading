"""s022: Slow MACD zero-line (momentum)

MACD line (EMA72 - EMA156) above zero long, below zero short.
"""


import numpy as np
import pandas as pd


NAME = 'Slow MACD zero-line'
FAMILY = 'momentum'
IDEA = 'MACD line (EMA72 - EMA156) above zero long, below zero short.'
PARAMS = {'fast': 72, 'slow': 156}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, slow):
    c = df["close"]
    m = ema(c, fast) - ema(c, slow)
    return ls(m > 0, m < 0)
