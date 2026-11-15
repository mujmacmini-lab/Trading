"""s095: Five-signal cross-family vote (combination)

EMA cross, 30d momentum, Donchian state, OBV trend and Keltner state: trade when at least four of five agree.
"""


import numpy as np
import pandas as pd


NAME = 'Five-signal cross-family vote'
FAMILY = 'combination'
IDEA = 'EMA cross, 30d momentum, Donchian state, OBV trend and Keltner state: trade when at least four of five agree.'
PARAMS = {'fast': 50, 'slow': 200, 'mom_n': 180, 'n_in': 120, 'n_out': 60, 'obv_n': 400, 'kel_n': 100, 'kel_k': 3.0, 'need': 3}


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


def signal(df, fast, slow, mom_n, n_in, n_out, obv_n, kel_n, kel_k, need):
    c = df["close"]
    o = obv(df)
    s = (np.sign(ema(c, fast) - ema(c, slow)) + np.sign(c / c.shift(mom_n) - 1).fillna(0)
         + donchian(df, n_in, n_out) + np.sign(o - sma(o, obv_n)).fillna(0) + keltner(df, kel_n, kel_k))
    return ls(s >= need, s <= -need)
