"""Indicator helpers. build.py copies the ones a strategy uses into its file."""
import numpy as np
import pandas as pd


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma(s, n):
    return s.rolling(n).mean()


def atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def rsi(s, n):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1.0 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def dmi(df, n):
    """Wilder +DI, -DI and ADX."""
    up = df["high"].diff()
    dn = -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    a = atr(df, n)
    pdi = 100 * pdm.ewm(alpha=1.0 / n, adjust=False).mean() / a
    mdi = 100 * mdm.ewm(alpha=1.0 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return pdi, mdi, dx.ewm(alpha=1.0 / n, adjust=False).mean()


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


def hold(entry, n):
    """Keep the most recent non-zero entry (+1/-1) for n bars."""
    return entry.where(entry != 0).ffill(limit=n - 1).fillna(0)


def trail(long_in, short_in, close, a, mult):
    """Enter on *_in, exit on an ATR trailing stop measured from the best close since entry."""
    li = np.asarray(long_in, dtype=bool)
    si = np.asarray(short_in, dtype=bool)
    c = close.to_numpy(dtype=float)
    av = a.to_numpy(dtype=float)
    pos = np.zeros(len(c))
    p = 0
    ext = 0.0
    for i in range(len(c)):
        if p == 1:
            ext = max(ext, c[i])
            if c[i] < ext - mult * av[i]:
                p = 0
        elif p == -1:
            ext = min(ext, c[i])
            if c[i] > ext + mult * av[i]:
                p = 0
        if p == 0:
            if li[i]:
                p, ext = 1, c[i]
            elif si[i]:
                p, ext = -1, c[i]
        pos[i] = p
    return pd.Series(pos, index=close.index)


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


def mom_vote(close, lookbacks):
    """Sum of the signs of the returns over several lookbacks."""
    v = pd.Series(0.0, index=close.index)
    for n in lookbacks:
        v = v + np.sign(close / close.shift(n) - 1).fillna(0)
    return v


def aligned(sig, direction):
    """Keep a position only where it points the same way as `direction`; otherwise flat."""
    return sig.where(np.sign(sig) == np.sign(direction), 0)


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


def kama(close, er_n, fast, slow):
    """Kaufman adaptive moving average."""
    x = close.to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) <= er_n:
        return pd.Series(out, index=close.index)
    change = close.diff(er_n).abs().to_numpy()
    noise = close.diff().abs().rolling(er_n).sum().to_numpy()
    f, s = 2.0 / (fast + 1), 2.0 / (slow + 1)
    out[er_n] = x[er_n]
    for i in range(er_n + 1, len(x)):
        er = change[i] / noise[i] if noise[i] > 0 else 0.0
        sc = (er * (f - s) + s) ** 2
        out[i] = out[i - 1] + sc * (x[i] - out[i - 1])
    return pd.Series(out, index=close.index)


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


def obv(df):
    return (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()
