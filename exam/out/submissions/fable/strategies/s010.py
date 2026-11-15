"""s010: SMA ribbon vote (trend following)

Price versus six SMAs (50..400 bars): long when at least two thirds are below price, short when two thirds are above.
"""


import numpy as np
import pandas as pd


NAME = 'SMA ribbon vote'
FAMILY = 'trend following'
IDEA = 'Price versus six SMAs (50..400 bars): long when at least two thirds are below price, short when two thirds are above.'
PARAMS = {'n1': 50, 'n2': 100, 'n3': 150, 'n4': 200, 'n5': 300, 'n6': 400, 'need': 0.34}


def sma(s, n):
    return s.rolling(n).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def signal(df, n1, n2, n3, n4, n5, n6, need):
    c = df["close"]
    spans = (n1, n2, n3, n4, n5, n6)
    score = pd.Series(0.0, index=c.index)
    for n in spans:
        score = score + np.sign(c - sma(c, n)).fillna(0) / len(spans)
    ready = sma(c, max(spans)).notna()
    return ls((score >= need) & ready, (score <= -need) & ready)
