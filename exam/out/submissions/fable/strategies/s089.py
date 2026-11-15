"""s089: SMA side plus MACD timing (combination)

Long when price is above SMA300 and the 24/52 MACD line is positive; short on the mirror; flat when they disagree.
"""


import numpy as np
import pandas as pd


NAME = 'SMA side plus MACD timing'
FAMILY = 'combination'
IDEA = 'Long when price is above SMA300 and the 24/52 MACD line is positive; short on the mirror; flat when they disagree.'
PARAMS = {'ma_n': 300, 'fast': 24, 'slow': 52}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, ma_n, fast, slow):
    c = df["close"]
    m = sma(c, ma_n)
    macd = ema(c, fast) - ema(c, slow)
    return ls((c > m) & (macd > 0), (c < m) & (macd < 0))
