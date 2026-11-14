"""s030: Dual-horizon momentum agreement (momentum)

Long only when both the 30-day and 90-day returns are positive, short when both negative, else flat.
"""


import numpy as np
import pandas as pd


NAME = 'Dual-horizon momentum agreement'
FAMILY = 'momentum'
IDEA = 'Long only when both the 30-day and 90-day returns are positive, short when both negative, else flat.'
PARAMS = {'fast': 180, 'slow': 540}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, fast, slow):
    c = df["close"]
    a = c / c.shift(fast) - 1
    b = c / c.shift(slow) - 1
    return ls((a > 0) & (b > 0), (a < 0) & (b < 0))
