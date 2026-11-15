"""s100: Seven-signal diversified average (combination)

Average of seven trend/momentum/breakout/volume signals; long above +0.3, short below -0.3, flat in between.
"""


import numpy as np
import pandas as pd


NAME = 'Seven-signal diversified average'
FAMILY = 'combination'
IDEA = 'Average of seven trend/momentum/breakout/volume signals; long above +0.3, short below -0.3, flat in between.'
PARAMS = {'fast': 50, 'slow': 200, 'ma_n': 300, 'mom1': 180, 'mom2': 360, 'n_in': 120, 'n_out': 60, 'kel_n': 100, 'kel_k': 3.0, 'obv_n': 400, 'level': 0.3}


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma(s, n):
    return s.rolling(n).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def ls(long_c, short_c):
    """+1 where long_c, -1 where short_c, else 0."""
    return pd.Series(np.where(long_c, 1, np.where(short_c, -1, 0)), index=long_c.index)


def latch(long_in, long_out, short_in, short_out):
    """Stateful position: enter on *_in, hold until *_out. Exits are processed before entries."""
    idx = long_in.index
    li, lo, si, so = (np.asarray(x, dtype=bool) for x in (long_in, long_out, short_in, short_out))
    pos = np.zeros(len(li))
    p = 0
    for i in range(len(li)):
        if p == 1 and lo[i]:
            p = 0
        elif p == -1 and so[i]:
            p = 0
        if p == 0:
            if li[i] and not lo[i]:
                p = 1
            elif si[i] and not so[i]:
                p = -1
        pos[i] = p
    return pd.Series(pos, index=idx)


def donchian(df, n_in, n_out):
    """Channel breakout state: enter on a close beyond the prior n_in-bar extreme, exit on the prior n_out-bar opposite extreme."""
    c = df["close"]
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch(c > hi, c < xl, c < lo, c > xh)


def keltner(df, n, k):
    """ATR-channel breakout state: enter beyond EMA +/- k*ATR, exit back at the EMA."""
    c = df["close"]
    m = ema(c, n)
    a = atr(df, n)
    return latch(c > m + k * a, c < m, c < m - k * a, c > m)


def obv(df):
    return (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()


def signal(df, fast, slow, ma_n, mom1, mom2, n_in, n_out, kel_n, kel_k, obv_n, level):
    c = df["close"]
    o = obv(df)
    parts = [
        np.sign(ema(c, fast) - ema(c, slow)),
        np.sign(c - sma(c, ma_n)).fillna(0),
        np.sign(c / c.shift(mom1) - 1).fillna(0),
        np.sign(c / c.shift(mom2) - 1).fillna(0),
        donchian(df, n_in, n_out),
        keltner(df, kel_n, kel_k),
        np.sign(o - sma(o, obv_n)).fillna(0),
    ]
    avg = sum(parts) / len(parts)
    ready = c.shift(max(mom1, mom2, ma_n, obv_n)).notna()
    return ls((avg > level) & ready, (avg < -level) & ready)
