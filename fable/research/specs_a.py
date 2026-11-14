"""Specs: trend following, momentum, breakout."""
import numpy as np
import pandas as pd

from helpers import *  # noqa: F401,F403
from reg import strat

TREND = "trend following"
MOM = "momentum"
BRK = "breakout"

# ----------------------------------------------------------------------------- trend following


@strat("EMA 50/200 cross", TREND, "Long when EMA50 is above EMA200, short when below (classic slow trend).",
       fast=50, slow=200)
def t01(df, fast, slow):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    return ls(f > s, f < s)


@strat("EMA 30/120 cross with ATR buffer", TREND,
       "EMA cross that only flips once the EMA gap exceeds a fraction of ATR, to skip whipsaw crosses.",
       fast=30, slow=120, atr_n=42, buffer=0.5)
def t02(df, fast, slow, atr_n, buffer):
    c = df["close"]
    gap = ema(c, fast) - ema(c, slow)
    band = buffer * atr(df, atr_n)
    return latch(gap > band, gap < 0, gap < -band, gap > 0)


@strat("SMA 300 with ATR hysteresis", TREND,
       "Long once price closes an ATR band above the 50-day SMA, out when it closes back below the SMA; mirrored short.",
       n=300, atr_n=42, band=1.0)
def t03(df, n, atr_n, band):
    c = df["close"]
    m = sma(c, n)
    b = band * atr(df, atr_n)
    return latch(c > m + b, c < m, c < m - b, c > m)


@strat("Triple EMA alignment", TREND,
       "Long only when EMA20 > EMA60 > EMA180 (all horizons aligned), short when fully inverted, otherwise flat.",
       fast=20, mid=60, slow=180)
def t04(df, fast, mid, slow):
    c = df["close"]
    a, b, d = ema(c, fast), ema(c, mid), ema(c, slow)
    return ls((a > b) & (b > d), (a < b) & (b < d))


@strat("Dual SMA side 50d/100d", TREND,
       "Long only when price is above both the 50-day and 100-day SMAs, short when below both, flat in between.",
       n1=300, n2=600)
def t05(df, n1, n2):
    c = df["close"]
    a, b = sma(c, n1), sma(c, n2)
    return ls((c > a) & (c > b), (c < a) & (c < b))


@strat("Linear-regression slope", TREND,
       "Sign of the least-squares slope of log price over 40 days: long when rising, short when falling.",
       n=240)
def t06(df, n):
    y = np.log(df["close"])
    x = pd.Series(np.arange(len(y), dtype=float), index=y.index)
    slope = y.rolling(n).cov(x) / x.rolling(n).var()
    return ls(slope > 0, slope < 0)


@strat("Supertrend", TREND, "ATR Supertrend stop-and-reverse with a wide multiplier.", atr_n=42, mult=5.0)
def t07(df, atr_n, mult):
    return supertrend(df, atr_n, mult)


@strat("Ichimoku cloud (daily-scaled)", TREND,
       "Ichimoku scaled x6 to 4h bars: long above the cloud with Tenkan > Kijun, short below with Tenkan < Kijun.",
       tenkan=54, kijun=156, span_b=312)
def t08(df, tenkan, kijun, span_b):
    h, l, c = df["high"], df["low"], df["close"]
    t = (h.rolling(tenkan).max() + l.rolling(tenkan).min()) / 2
    k = (h.rolling(kijun).max() + l.rolling(kijun).min()) / 2
    sa = ((t + k) / 2).shift(kijun)
    sb = ((h.rolling(span_b).max() + l.rolling(span_b).min()) / 2).shift(kijun)
    top = pd.concat([sa, sb], axis=1).max(axis=1, skipna=False)
    bot = pd.concat([sa, sb], axis=1).min(axis=1, skipna=False)
    return ls((c > top) & (t > k), (c < bot) & (t < k))


@strat("Donchian midline trend", TREND,
       "Long when price is in the upper part of its 40-day high-low range, short in the lower part, with a dead zone.",
       n=240, upper=0.55, lower=0.45, mid=0.5)
def t09(df, n, upper, lower, mid):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    pos = (df["close"] - ll) / (hh - ll)
    return latch(pos > upper, pos < mid, pos < lower, pos > mid)


@strat("SMA ribbon vote", TREND,
       "Price versus six SMAs (50..400 bars): long when at least two thirds are below price, short when two thirds are above.",
       n1=50, n2=100, n3=150, n4=200, n5=300, n6=400, need=0.34)
def t10(df, n1, n2, n3, n4, n5, n6, need):
    c = df["close"]
    spans = (n1, n2, n3, n4, n5, n6)
    score = pd.Series(0.0, index=c.index)
    for n in spans:
        score = score + np.sign(c - sma(c, n)).fillna(0) / len(spans)
    ready = sma(c, max(spans)).notna()
    return ls((score >= need) & ready, (score <= -need) & ready)


@strat("EMA 200 slope and side", TREND,
       "Long when EMA200 is rising and price is above it, short when falling and price is below, flat when they disagree.",
       n=200, slope_n=30)
def t11(df, n, slope_n):
    c = df["close"]
    e = ema(c, n)
    return ls((e > e.shift(slope_n)) & (c > e), (e < e.shift(slope_n)) & (c < e))


@strat("Hull MA slope", TREND, "Direction of an 80-day Hull moving average (low-lag, so it needs a long window to avoid whipsaw).", n=480, slope_n=30)
def t12(df, n, slope_n):
    c = df["close"]
    h = wma(2 * wma(c, n // 2) - wma(c, n), int(round(n ** 0.5)))
    return ls(h > h.shift(slope_n), h < h.shift(slope_n))


@strat("Chandelier trend", TREND,
       "Enter on a 20-day closing high/low, exit on a 4-ATR trailing stop from the best close since entry.",
       n=120, atr_n=42, mult=4.0)
def t13(df, n, atr_n, mult):
    c = df["close"]
    hi = c.rolling(n).max().shift(1)
    lo = c.rolling(n).min().shift(1)
    return trail(c > hi, c < lo, c, atr(df, atr_n), mult)


@strat("Directional movement (DI) trend", TREND,
       "Long when Wilder +DI(84) is above -DI(84), short when below (two-week directional pressure).",
       n=84, gap=3.0)
def t14(df, n, gap):
    pdi, mdi, _ = dmi(df, n)
    d = pdi - mdi
    return latch(d > gap, d < 0, d < -gap, d > 0)


@strat("Long-only golden regime", TREND,
       "Long only while EMA50 > EMA200 and price is above EMA50; flat otherwise (never short).",
       fast=50, slow=200)
def t15(df, fast, slow):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    return ls((f > s) & (c > f), pd.Series(False, index=c.index))


@strat("Two-speed EMA consensus", TREND,
       "Trade only when a fast (20/100) and a slow (50/200) EMA system agree; flat when they disagree.",
       f1=20, s1=100, f2=50, s2=200)
def t16(df, f1, s1, f2, s2):
    c = df["close"]
    a = np.sign(ema(c, f1) - ema(c, s1))
    b = np.sign(ema(c, f2) - ema(c, s2))
    return ls((a > 0) & (b > 0), (a < 0) & (b < 0))


# ----------------------------------------------------------------------------- momentum


@strat("Time-series momentum 30d", MOM, "Sign of the 30-day (180-bar) return.", n=180)
def m01(df, n):
    ret = df["close"] / df["close"].shift(n) - 1
    return ls(ret > 0, ret < 0)


@strat("Time-series momentum 60d", MOM, "Sign of the 60-day (360-bar) return.", n=360)
def m02(df, n):
    ret = df["close"] / df["close"].shift(n) - 1
    return ls(ret > 0, ret < 0)


@strat("Momentum majority vote 15/30/60d", MOM,
       "Majority vote of the signs of the 15-, 30- and 60-day returns.", n1=90, n2=180, n3=360)
def m03(df, n1, n2, n3):
    v = mom_vote(df["close"], (n1, n2, n3))
    ready = df["close"].shift(max(n1, n2, n3)).notna()
    return ls((v > 0) & ready, (v < 0) & ready)


@strat("Momentum vote 30/60/90/120d", MOM,
       "Signs of the 1-, 2-, 3- and 4-month returns vote: long on a majority up, short on a majority down, flat on a 2-2 tie.",
       n1=180, n2=360, n3=540, n4=720)
def m04(df, n1, n2, n3, n4):
    v = mom_vote(df["close"], (n1, n2, n3, n4))
    return ls(v > 0, v < 0)


@strat("Vol-scaled momentum with threshold", MOM,
       "30-day return in units of its own volatility: enter beyond +/-0.5 sigma, exit when it crosses zero.",
       n=180, enter=0.5)
def m05(df, n, enter):
    c = df["close"]
    z = (c / c.shift(n) - 1) / (c.pct_change().rolling(n).std() * n ** 0.5)
    return latch(z > enter, z < 0, z < -enter, z > 0)


@strat("Slow MACD zero-line", MOM, "MACD line (EMA72 - EMA156) above zero long, below zero short.", fast=72, slow=156)
def m06(df, fast, slow):
    c = df["close"]
    m = ema(c, fast) - ema(c, slow)
    return ls(m > 0, m < 0)


@strat("MACD line and histogram agreement", MOM,
       "Long only when the 48/104 MACD line is positive and above its signal line; short on the mirror; else flat.",
       fast=48, slow=104, sig=36)
def m07(df, fast, slow, sig):
    c = df["close"]
    m = ema(c, fast) - ema(c, slow)
    s = ema(m, sig)
    return ls((m > 0) & (m > s), (m < 0) & (m < s))


@strat("Smoothed rate of change", MOM, "EMA-smoothed 20-day rate of change: long when positive, short when negative.",
       n=120, smooth=30)
def m08(df, n, smooth):
    roc = ema(df["close"].pct_change(n), smooth)
    return ls(roc > 0, roc < 0)


@strat("Skip-recent momentum", MOM,
       "60-day momentum that ignores the latest 5 days (classic skip-period momentum), to avoid short-term reversal noise.",
       n=360, skip=30)
def m09(df, n, skip):
    c = df["close"]
    ret = c.shift(skip) / c.shift(n) - 1
    return ls(ret > 0, ret < 0)


@strat("Long-window RSI regime", MOM,
       "RSI(84) as a momentum gauge: long above 55, short below 45, exit on a cross of 50.",
       n=84, upper=55, lower=45, mid=50)
def m10(df, n, upper, lower, mid):
    x = rsi(df["close"], n)
    return latch(x > upper, x < mid, x < lower, x > mid)


@strat("True Strength Index", MOM, "Double-smoothed momentum (TSI) above/below zero.", r=150, s=75)
def m11(df, r, s):
    d = df["close"].diff()
    tsi = ema(ema(d, r), s) / ema(ema(d.abs(), r), s)
    return ls(tsi > 0, tsi < 0)


@strat("Volume-weighted momentum", MOM,
       "Sign of the volume-weighted average bar return over 30 days (moves on heavy volume count more).", n=180)
def m12(df, n):
    r = df["close"].pct_change()
    vw = (r * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()
    return ls(vw > 0, vw < 0)


@strat("On-balance volume trend", MOM, "OBV above its 400-bar average long, below short (volume-flow momentum).", n=400)
def m13(df, n):
    o = obv(df)
    m = sma(o, n)
    return ls(o > m, o < m)


@strat("Dual-horizon momentum agreement", MOM,
       "Long only when both the 30-day and 90-day returns are positive, short when both negative, else flat.",
       fast=180, slow=540)
def m14(df, fast, slow):
    c = df["close"]
    a = c / c.shift(fast) - 1
    b = c / c.shift(slow) - 1
    return ls((a > 0) & (b > 0), (a < 0) & (b < 0))


@strat("Aroon oscillator", MOM,
       "Aroon(150): long when the most recent 25-day high is much fresher than the most recent low, short on the mirror.",
       n=150, level=30)
def m15(df, n, level):
    up = df["high"].rolling(n + 1).apply(np.argmax, raw=True) * 100.0 / n
    dn = df["low"].rolling(n + 1).apply(np.argmin, raw=True) * 100.0 / n
    osc = up - dn
    return latch(osc > level, osc < 0, osc < -level, osc > 0)


@strat("Range-position momentum", MOM,
       "Smoothed position of price inside its 50-day range (slow stochastic): long above 60%, short below 40%, exit at 50%.",
       n=300, smooth=6, upper=0.6, lower=0.4, mid=0.5)
def m16(df, n, smooth, upper, lower, mid):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    k = sma((df["close"] - ll) / (hh - ll), smooth)
    return latch(k > upper, k < mid, k < lower, k > mid)


# ----------------------------------------------------------------------------- breakout


@strat("Donchian 20d/10d", BRK, "Enter on a 20-day (120-bar) high/low breakout, exit on the opposite 10-day extreme.",
       n_in=120, n_out=60)
def b01(df, n_in, n_out):
    return donchian(df, n_in, n_out)


@strat("Donchian 40/20 bars", BRK, "Faster channel: enter on a 40-bar breakout, exit on the opposite 20-bar extreme.",
       n_in=40, n_out=20)
def b02(df, n_in, n_out):
    return donchian(df, n_in, n_out)


@strat("Trend-filtered fast Donchian", BRK,
       "20-bar breakouts taken only in the direction of the 50-day SMA; exit on the opposite 10-bar extreme.",
       n_in=20, n_out=10, trend_n=300)
def b03(df, n_in, n_out, trend_n):
    c = df["close"]
    m = sma(c, trend_n)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & (c > m), c < xl, (c < lo) & (c < m), c > xh)


@strat("Keltner breakout 100/3", BRK,
       "Enter when price closes 3 ATR beyond EMA100, exit when it returns to the EMA.", n=100, k=3.0)
def b04(df, n, k):
    return keltner(df, n, k)


@strat("Keltner breakout 20/2", BRK, "Fast ATR channel: enter 2 ATR beyond EMA20, exit back at the EMA.", n=20, k=2.0)
def b05(df, n, k):
    return keltner(df, n, k)


@strat("Keltner breakout 50/2", BRK, "Medium ATR channel: enter 2 ATR beyond EMA50, exit back at the EMA.", n=50, k=2.0)
def b06(df, n, k):
    return keltner(df, n, k)


@strat("Bollinger breakout with 60d momentum", BRK,
       "Close outside the 2-sigma band of SMA100 (strength, not reversal), held to the SMA, kept only when it agrees with the 60-day return.",
       n=100, k=2.0, mom_n=360)
def b07(df, n, k, mom_n):
    c = df["close"]
    m = sma(c, n)
    sd = c.rolling(n).std()
    state = latch(c > m + k * sd, c < m, c < m - k * sd, c > m)
    return aligned(state, c / c.shift(mom_n) - 1)


@strat("Closing-high breakout with ATR trail", BRK,
       "Enter on a 15-day closing high (only above SMA300) or closing low (only below it); exit on a 3.5-ATR trailing stop.",
       n=90, atr_n=42, mult=3.5, trend_n=300)
def b08(df, n, atr_n, mult, trend_n):
    c = df["close"]
    m = sma(c, trend_n)
    return trail((c > c.rolling(n).max().shift(1)) & (c > m), (c < c.rolling(n).min().shift(1)) & (c < m),
                 c, atr(df, atr_n), mult)


@strat("Volume-confirmed breakout", BRK,
       "10-day channel breakout in the direction of the 30/60/90-day momentum vote, on a bar with well-above-average volume; exit on the 5-day opposite extreme.",
       n_in=60, n_out=30, vol_n=120, vol_mult=1.5, n1=180, n2=360, n3=540)
def b09(df, n_in, n_out, vol_n, vol_mult, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    big = df["volume"] > vol_mult * sma(df["volume"], vol_n).shift(1)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & big & (v > 0), c < xl, (c < lo) & big & (v < 0), c > xh)


@strat("Keltner 20/2 in voted trend", BRK,
       "Fast ATR-channel breakouts (2 ATR beyond EMA20, exit at the EMA) taken only in the direction of the 30/60/90-day momentum vote.",
       n=20, k=2.0, n1=180, n2=360, n3=540)
def b10(df, n, k, n1, n2, n3):
    state = keltner(df, n, k)
    v = mom_vote(df["close"], (n1, n2, n3))
    return ls((state > 0) & (v > 0), (state < 0) & (v < 0))


@strat("Previous-week range breakout", BRK,
       "Close above last calendar week's high (long) or below its low (short), exit at last week's midpoint; kept only with the 30/60/90-day momentum vote.",
       exit_frac=0.5, n1=180, n2=360, n3=540)
def b11(df, exit_frac, n1, n2, n3):
    c = df["close"]
    wid = pd.Series(np.cumsum((df.index.dayofweek == 0) & (df.index.hour == 0)), index=df.index)
    wh = df["high"].groupby(wid).max().shift(1)
    wl = df["low"].groupby(wid).min().shift(1)
    ph, pl = wid.map(wh), wid.map(wl)
    mid = pl + exit_frac * (ph - pl)
    return aligned(latch(c > ph, c < mid, c < pl, c > mid), mom_vote(c, (n1, n2, n3)))


@strat("Previous-month range breakout", BRK,
       "Long on a close above last calendar month's high, short below its low; exit at last month's midpoint.",
       exit_frac=0.5)
def b12(df, exit_frac):
    c = df["close"]
    mid_ = pd.Series(np.cumsum((df.index.day == 1) & (df.index.hour == 0)), index=df.index)
    ph = mid_.map(df["high"].groupby(mid_).max().shift(1))
    pl = mid_.map(df["low"].groupby(mid_).min().shift(1))
    mid = pl + exit_frac * (ph - pl)
    return latch(c > ph, c < mid, c < pl, c > mid)


@strat("Dual-channel breakout", BRK,
       "10-day breakouts taken only on the correct side of the 40-day channel midline; exit on the 5-day opposite extreme.",
       n_in=60, n_out=30, n_big=240)
def b13(df, n_in, n_out, n_big):
    c = df["close"]
    mid = (df["high"].rolling(n_big).max() + df["low"].rolling(n_big).min()) / 2
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & (c > mid), c < xl, (c < lo) & (c < mid), c > xh)


@strat("Swing-pivot breakout", BRK,
       "Close above the last confirmed swing high (pivot with ~3 days each side) is long, below the last swing low is short; kept only with the 60-day return.",
       k=20, mom_n=360)
def b14(df, k, mom_n):
    h, l, c = df["high"], df["low"], df["close"]
    w = 2 * k + 1
    ph = h.shift(k).where(h.shift(k) == h.rolling(w).max()).ffill()
    pl = l.shift(k).where(l.shift(k) == l.rolling(w).min()).ffill()
    return aligned(latch(c > ph, c < pl, c < pl, c > ph), c / c.shift(mom_n) - 1)


@strat("Daily-close 30d/15d breakout", BRK,
       "Turtle-style rule on daily closes only (the 20:00 UTC bar): enter on a 30-day closing high/low, exit on the 15-day opposite.",
       n_in=30, n_out=15, close_hour=20)
def b15(df, n_in, n_out, close_hour):
    d = df["close"][df.index.hour == close_hour]
    hi = d.rolling(n_in).max().shift(1)
    lo = d.rolling(n_in).min().shift(1)
    xh = d.rolling(n_out).max().shift(1)
    xl = d.rolling(n_out).min().shift(1)
    return latch(d > hi, d < xl, d < lo, d > xh).reindex(df.index).ffill().fillna(0)


@strat("Rolling-VWAP band breakout", BRK,
       "Enter when price closes 2 sigma beyond the 20-day volume-weighted average price; exit back at the VWAP.",
       n=120, k=2.0)
def b16(df, n, k):
    c = df["close"]
    tp = (df["high"] + df["low"] + c) / 3
    vwap = (tp * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()
    sd = (c - vwap).rolling(n).std()
    return latch(c > vwap + k * sd, c < vwap, c < vwap - k * sd, c > vwap)
