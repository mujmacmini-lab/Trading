"""s012: Hull MA slope (trend following)

Direction of an 80-day Hull moving average (low-lag, so it needs a long window to avoid whipsaw).
"""


import numpy as np
import pandas as pd


NAME = 'Hull MA slope'
FAMILY = 'trend following'
IDEA = 'Direction of an 80-day Hull moving average (low-lag, so it needs a long window to avoid whipsaw).'
PARAMS = {'n': 480, 'slope_n': 30}


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def wma(s, n):
    """Linearly weighted moving average (most recent bar has weight n)."""
    x = s.to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    ok = np.nonzero(~np.isnan(x))[0]
    if len(ok) == 0 or len(x) - ok[0] < n:
        return pd.Series(out, index=s.index)
    st = ok[0]
    w = np.arange(n, 0, -1, dtype=float)
    out[st + n - 1:] = np.convolve(x[st:], w, mode="valid") / w.sum()
    return pd.Series(out, index=s.index)


def signal(df, n, slope_n):
    c = df["close"]
    h = wma(2 * wma(c, n // 2) - wma(c, n), int(round(n ** 0.5)))
    return ls(h > h.shift(slope_n), h < h.shift(slope_n))
