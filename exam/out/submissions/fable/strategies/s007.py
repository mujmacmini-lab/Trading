"""s007: Supertrend (trend following)

ATR Supertrend stop-and-reverse with a wide multiplier.
"""


import numpy as np
import pandas as pd


NAME = 'Supertrend'
FAMILY = 'trend following'
IDEA = 'ATR Supertrend stop-and-reverse with a wide multiplier.'
PARAMS = {'atr_n': 42, 'mult': 5.0}


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def supertrend(df, n, mult):
    """Supertrend direction (+1 / -1)."""
    a = atr(df, n).to_numpy(dtype=float)
    c = df["close"].to_numpy(dtype=float)
    mid = ((df["high"] + df["low"]) / 2).to_numpy(dtype=float)
    ub = mid + mult * a
    lb = mid - mult * a
    out = np.zeros(len(c))
    d = 1
    for i in range(1, len(c)):
        if not (ub[i] < ub[i - 1] or c[i - 1] > ub[i - 1]):
            ub[i] = ub[i - 1]
        if not (lb[i] > lb[i - 1] or c[i - 1] < lb[i - 1]):
            lb[i] = lb[i - 1]
        if d == 1 and c[i] < lb[i]:
            d = -1
        elif d == -1 and c[i] > ub[i]:
            d = 1
        out[i] = d
    return pd.Series(out, index=df.index)


def signal(df, atr_n, mult):
    return supertrend(df, atr_n, mult)
