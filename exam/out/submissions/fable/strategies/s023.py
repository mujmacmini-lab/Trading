"""s023: MACD line and histogram agreement (momentum)

Long only when the 48/104 MACD line is positive and above its signal line; short on the mirror; else flat.
"""


import numpy as np
import pandas as pd


NAME = 'MACD line and histogram agreement'
FAMILY = 'momentum'
IDEA = 'Long only when the 48/104 MACD line is positive and above its signal line; short on the mirror; else flat.'
PARAMS = {'fast': 48, 'slow': 104, 'sig': 36}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, slow, sig):
    c = df["close"]
    m = ema(c, fast) - ema(c, slow)
    s = ema(m, sig)
    return ls((m > 0) & (m > s), (m < 0) & (m < s))
