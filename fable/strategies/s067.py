"""s067: Volatility-adaptive Donchian (volatility)

Channel breakout whose lookback stretches when short-term vol is high and shrinks when calm; a side is held only on the matching side of SMA300.
"""


import numpy as np
import pandas as pd


NAME = 'Volatility-adaptive Donchian'
FAMILY = 'volatility'
IDEA = 'Channel breakout whose lookback stretches when short-term vol is high and shrinks when calm; a side is held only on the matching side of SMA300.'
PARAMS = {'base': 80, 'vol_fast': 42, 'vol_slow': 540, 'lo_mult': 0.5, 'hi_mult': 2.0, 'trend_n': 300}


def sma(s, n):
    return s.rolling(n).mean()


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


def signal(df, base, vol_fast, vol_slow, lo_mult, hi_mult, trend_n):
    r = df["close"].pct_change()
    mult = (r.rolling(vol_fast).std() / r.rolling(vol_slow).std()).clip(lo_mult, hi_mult).to_numpy()
    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    c = df["close"].to_numpy(dtype=float)
    pos = np.zeros(len(c))
    p = 0
    for i in range(len(c)):
        if np.isnan(mult[i]):
            continue
        n = int(round(base * mult[i]))
        x = max(2, n // 2)
        if i < n:
            continue
        if p == 1 and c[i] < l[i - x:i].min():
            p = 0
        elif p == -1 and c[i] > h[i - x:i].max():
            p = 0
        if p == 0:
            if c[i] > h[i - n:i].max():
                p = 1
            elif c[i] < l[i - n:i].min():
                p = -1
        pos[i] = p
    return aligned(pd.Series(pos, index=df.index), df["close"] - sma(df["close"], trend_n))
