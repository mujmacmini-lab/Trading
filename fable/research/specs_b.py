"""Specs: mean reversion, volatility, regime filters, combinations."""
import numpy as np
import pandas as pd

from helpers import *  # noqa: F401,F403
from reg import strat

MR = "mean reversion"
VOL = "volatility"
REG = "regime filter"
COMBO = "combination"

# ----------------------------------------------------------------------------- mean reversion
# Plain fading loses on BTC 4h after costs (see FINAL.md); every rule here fades a short-term
# move back toward a slower trend.


@strat("RSI(4) pullback in voted trend", MR,
       "With the 15/30/60-day momentum vote up, buy RSI(4) < 25 and exit at RSI > 60 or when the trend vote flips; mirrored short.",
       n1=90, n2=180, n3=360, rsi_n=4, low=25, exit_level=60)
def r01(df, n1, n2, n3, rsi_n, low, exit_level):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    x = rsi(c, rsi_n)
    up, dn = v > 0, v < 0
    return latch(up & (x < low), (x > exit_level) | ~up, dn & (x > 100 - low), (x < 100 - exit_level) | ~dn)


@strat("Stop-run reclaim in slow trend", MR,
       "With the 30/60/90-day vote up, a bar that undercuts the prior 5-day low but closes back above it is bought for 4 days; mirrored short.",
       n=30, hold_n=24, n1=180, n2=360, n3=540)
def r02(df, n, hold_n, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    pl = df["low"].rolling(n).min().shift(1)
    ph = df["high"].rolling(n).max().shift(1)
    e = ls((df["low"] < pl) & (c > pl) & (v > 0), (df["high"] > ph) & (c < ph) & (v < 0))
    return hold(e, hold_n)


@strat("Bollinger pullback in trend", MR,
       "In a 30-day uptrend buy a close 1.5 sigma below SMA30, exit at the SMA; mirrored short.",
       trend_n=180, n=30, k=1.5)
def r03(df, trend_n, n, k):
    c = df["close"]
    z = (c - sma(c, n)) / c.rolling(n).std()
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return latch(up & (z < -k), (z > 0) | ~up, dn & (z > k), (z < 0) | ~dn)


@strat("Pullback-resumption entry", MR,
       "In a voted uptrend, after at least 6 bars below EMA50 buy the first close back above it and hold until price closes below it again; mirrored short.",
       n=50, k=6, n1=180, n2=360, n3=540)
def r04(df, n, k, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    e = ema(c, n)
    below, above = c < e, c > e
    was_below = below.shift(1).rolling(k).sum() == k
    was_above = above.shift(1).rolling(k).sum() == k
    up, dn = v > 0, v < 0
    return latch(up & above & was_below, below | ~up, dn & below & was_above, above | ~dn)


@strat("Williams %R pullback in trend", MR,
       "With price above SMA300, buy when %R(20) drops below -90 and exit above -40 or on trend loss; mirrored short.",
       trend_n=300, n=20, low=-90, exit_level=-40)
def r05(df, trend_n, n, low, exit_level):
    c = df["close"]
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    w = -100 * (hh - c) / (hh - ll)
    m = sma(c, trend_n)
    up, dn = c > m, c < m
    return latch(up & (w < low), (w > exit_level) | ~up, dn & (w > -100 - low), (w < -100 - exit_level) | ~dn)


@strat("Failed-breakdown reclaim", MR,
       "In an uptrend, a bar that pierces the prior 20-bar low but closes back above it (stop-run) is bought for 4 days; mirrored short.",
       n=20, hold_n=24, n1=90, n2=180, n3=360)
def r06(df, n, hold_n, n1, n2, n3):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    pl = df["low"].rolling(n).min().shift(1)
    ph = df["high"].rolling(n).max().shift(1)
    e = ls((df["low"] < pl) & (c > pl) & (v > 0), (df["high"] > ph) & (c < ph) & (v < 0))
    return hold(e, hold_n)


@strat("EMA-zone pullback", MR,
       "In an EMA50>EMA200 uptrend buy a dip of 1 ATR below EMA50, exit 1 ATR above it or on trend loss; mirrored short.",
       fast=50, slow=200, atr_n=42, depth=1.0)
def r07(df, fast, slow, atr_n, depth):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    b = depth * atr(df, atr_n)
    up, dn = f > s, f < s
    return latch(up & (c < f - b), (c > f + b) | ~up, dn & (c > f + b), (c < f - b) | ~dn)


@strat("Bull-regime deep dip (long-only)", MR,
       "Above the 100-day SMA, buy a close 2 sigma below SMA50 and exit back at SMA50; never short.",
       regime_n=600, n=50, k=2.0)
def r08(df, regime_n, n, k):
    c = df["close"]
    z = (c - sma(c, n)) / c.rolling(n).std()
    none = pd.Series(False, index=c.index)
    return latch((c > sma(c, regime_n)) & (z < -k), z > 0, none, none)


@strat("VWAP pullback in voted trend", MR,
       "With the momentum vote up, buy when price closes 1 ATR below the 7-day rolling VWAP and exit back at the VWAP or on a vote flip; mirrored short.",
       n1=90, n2=180, n3=360, vwap_n=42, atr_n=42, depth=1.0)
def r09(df, n1, n2, n3, vwap_n, atr_n, depth):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    tp = (df["high"] + df["low"] + c) / 3
    vwap = (tp * df["volume"]).rolling(vwap_n).sum() / df["volume"].rolling(vwap_n).sum()
    b = depth * atr(df, atr_n)
    up, dn = v > 0, v < 0
    return latch(up & (c < vwap - b), (c > vwap) | ~up, dn & (c > vwap + b), (c < vwap) | ~dn)


@strat("Trend-channel lower-half entry", MR,
       "In a 30-day uptrend buy only when price sits in the lower third of its 5-day range, exit in the upper third; mirrored short.",
       trend_n=180, n=30, low=0.33, high=0.67)
def r10(df, trend_n, n, low, high):
    c = df["close"]
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    p = (c - ll) / (hh - ll)
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return latch(up & (p < low), (p > high) | ~up, dn & (p > 1 - low), (p < 1 - high) | ~dn)


# ----------------------------------------------------------------------------- volatility


@strat("Shock continuation", VOL,
       "A 12-hour move larger than 3 sigma (of recent bar volatility) is followed in its direction for 2 days.",
       k_bars=3, k=3.0, hold_n=12, vol_n=180)
def v01(df, k_bars, k, hold_n, vol_n):
    c = df["close"]
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    return hold(ls(z > k, z < -k), hold_n)


@strat("Momentum vote with volatility ceiling", VOL,
       "Momentum vote (15/30/60d) traded only while 7-day realised vol is below 1.5x its 90-day level; flat in vol spikes.",
       n1=90, n2=180, n3=360, vol_fast=42, vol_slow=540, ceiling=1.5)
def v02(df, n1, n2, n3, vol_fast, vol_slow, ceiling):
    c = df["close"]
    r = c.pct_change()
    v = mom_vote(c, (n1, n2, n3))
    calm = r.rolling(vol_fast).std() < ceiling * r.rolling(vol_slow).std()
    return ls((v > 0) & calm, (v < 0) & calm)


@strat("Bollinger squeeze breakout", VOL,
       "After band width falls into the bottom quartile of the last 40 days, trade the next 40-bar breakout in the direction of the momentum vote; exit at the SMA.",
       n=40, window=240, q=0.25, recent=6, n1=180, n2=360, n3=540)
def v03(df, n, window, q, recent, n1, n2, n3):
    c = df["close"]
    m = sma(c, n)
    width = c.rolling(n).std() / m
    squeezed = width.rolling(window).rank(pct=True).rolling(recent).min() < q
    hi = df["high"].rolling(n).max().shift(1)
    lo = df["low"].rolling(n).min().shift(1)
    v = mom_vote(c, (n1, n2, n3))
    return latch((c > hi) & squeezed & (v > 0), c < m, (c < lo) & squeezed & (v < 0), c > m)


@strat("ATR-contraction breakout", VOL,
       "When short-term ATR has dropped below 80% of long-term ATR, trade the next 40-bar breakout; exit on the 20-bar opposite extreme.",
       atr_fast=12, atr_slow=120, ratio=0.8, recent=12, n_in=40, n_out=20)
def v04(df, atr_fast, atr_slow, ratio, recent, n_in, n_out):
    c = df["close"]
    quiet = (atr(df, atr_fast) / atr(df, atr_slow)).rolling(recent).min() < ratio
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & quiet, c < xl, (c < lo) & quiet, c > xh)


@strat("Uptrend with high-vol kill switch (long-only)", VOL,
       "Long above SMA300 except when 7-day realised vol is in the top decile of the last 90 days; never short.",
       n=300, vol_n=42, window=540, cap=0.9)
def v05(df, n, vol_n, window, cap):
    c = df["close"]
    rank = c.pct_change().rolling(vol_n).std().rolling(window).rank(pct=True)
    return ls((c > sma(c, n)) & (rank < cap), pd.Series(False, index=c.index))


@strat("Volatility stop-and-reverse", VOL,
       "Flip when price closes more than 6 ATR(84) against the best close since the last flip; a side is held only while the 1-4 month momentum vote agrees.",
       atr_n=84, mult=6.0, n1=180, n2=360, n3=540, n4=720)
def v06(df, atr_n, mult, n1, n2, n3, n4):
    c = df["close"].to_numpy(dtype=float)
    a = atr(df, atr_n).to_numpy(dtype=float)
    pos = np.zeros(len(c))
    p = 0
    hi = lo = c[0]
    for i in range(1, len(c)):
        hi = max(hi, c[i])
        lo = min(lo, c[i])
        if p <= 0 and c[i] > lo + mult * a[i]:
            p, hi = 1, c[i]
        elif p >= 0 and c[i] < hi - mult * a[i]:
            p, lo = -1, c[i]
        pos[i] = p
    return aligned(pd.Series(pos, index=df.index), mom_vote(df["close"], (n1, n2, n3, n4)))


@strat("Expanding-bandwidth trend", VOL,
       "Trade the side of SMA60 only while band width is above its 20-day average (volatility expanding) and the 60-day return agrees; else flat.",
       n=60, avg_n=120, mom_n=360)
def v07(df, n, avg_n, mom_n):
    c = df["close"]
    m = sma(c, n)
    width = c.rolling(n).std() / m
    expanding = width > sma(width, avg_n)
    return aligned(ls((c > m) & expanding, (c < m) & expanding), c / c.shift(mom_n) - 1)


@strat("Up/down semivariance ratio", VOL,
       "Compare 30-day upside and downside realised variance: long when upside dominates, short when downside dominates.",
       n=180, ratio=1.2)
def v08(df, n, ratio):
    r = df["close"].pct_change()
    up = (r.clip(lower=0) ** 2).rolling(n).sum()
    dn = (r.clip(upper=0) ** 2).rolling(n).sum()
    q = up / dn
    return latch(q > ratio, q < 1, q < 1 / ratio, q > 1)


@strat("Volatility-adaptive Donchian", VOL,
       "Channel breakout whose lookback stretches when short-term vol is high and shrinks when calm; a side is held only on the matching side of SMA300.",
       base=80, vol_fast=42, vol_slow=540, lo_mult=0.5, hi_mult=2.0, trend_n=300)
def v09(df, base, vol_fast, vol_slow, lo_mult, hi_mult, trend_n):
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


@strat("Calm uptrend (long-only)", VOL,
       "Long only when price is above SMA300 and 7-day realised vol is below its 90-day median (quiet grind higher); never short.",
       n=300, vol_n=42, window=540)
def v10(df, n, vol_n, window):
    c = df["close"]
    vol = c.pct_change().rolling(vol_n).std()
    calm = vol < vol.rolling(window).median()
    return ls((c > sma(c, n)) & calm, pd.Series(False, index=c.index))


@strat("Expansion-confirmed breakout", VOL,
       "A 40-bar breakout is taken only if short-term ATR is already above long-term ATR (range expansion); exit on the 20-bar opposite extreme.",
       atr_fast=12, atr_slow=120, ratio=1.1, n_in=40, n_out=20)
def v11(df, atr_fast, atr_slow, ratio, n_in, n_out):
    c = df["close"]
    hot = atr(df, atr_fast) > ratio * atr(df, atr_slow)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & hot, c < xl, (c < lo) & hot, c > xh)


@strat("Volatility-normalised momentum", VOL,
       "30-day sum of bar returns each divided by the prevailing 7-day volatility, so calm-period moves count as much as wild ones; trade its sign.",
       n=180, vol_n=42)
def v12(df, n, vol_n):
    r = df["close"].pct_change()
    s = (r / r.rolling(vol_n).std().shift(1)).rolling(n).sum()
    return ls(s > 0, s < 0)


@strat("Trend-aligned shock", VOL,
       "A 1-day move beyond 2.5 sigma is followed for 3 days, but only when it agrees with the 30-day trend.",
       k_bars=6, k=2.5, hold_n=18, vol_n=180, trend_n=180)
def v13(df, k_bars, k, hold_n, vol_n, trend_n):
    c = df["close"]
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    up, dn = c > c.shift(trend_n), c < c.shift(trend_n)
    return hold(ls((z > k) & up, (z < -k) & dn), hold_n)


@strat("Volatility-regime speed switch", VOL,
       "Use a slow 30d/15d channel when realised vol is above its 90-day norm and a fast 40/20-bar channel when it is below.",
       vol_fast=42, vol_slow=540, slow_in=180, slow_out=90, fast_in=40, fast_out=20)
def v14(df, vol_fast, vol_slow, slow_in, slow_out, fast_in, fast_out):
    r = df["close"].pct_change()
    high_vol = r.rolling(vol_fast).std() > r.rolling(vol_slow).std()
    slow = donchian(df, slow_in, slow_out)
    fast = donchian(df, fast_in, fast_out)
    return slow.where(high_vol, fast)


# ----------------------------------------------------------------------------- regime filters


@strat("ADX-gated momentum vote", REG,
       "30/60/90-day momentum vote, traded only while ADX(14) > 20 (a trend is actually present); flat otherwise.",
       n1=180, n2=360, n3=540, adx_n=14, level=20)
def g01(df, n1, n2, n3, adx_n, level):
    v = mom_vote(df["close"], (n1, n2, n3))
    on = dmi(df, adx_n)[2] > level
    return ls((v > 0) & on, (v < 0) & on)


@strat("ADX-gated EMA cross", REG, "EMA 50/200 direction, traded only while ADX(14) > 20.",
       fast=50, slow=200, adx_n=14, level=20)
def g02(df, fast, slow, adx_n, level):
    c = df["close"]
    f, s = ema(c, fast), ema(c, slow)
    on = dmi(df, adx_n)[2] > level
    return ls((f > s) & on, (f < s) & on)


@strat("Bull/bear-aligned momentum", REG,
       "30-day momentum, but longs only above the 100-day SMA and shorts only below it.",
       n=180, regime_n=600)
def g03(df, n, regime_n):
    c = df["close"]
    ret = c / c.shift(n) - 1
    m = sma(c, regime_n)
    return ls((ret > 0) & (c > m), (ret < 0) & (c < m))


@strat("Efficiency-ratio regime", REG,
       "Kaufman efficiency ratio over 20 days: when the path is efficient (> 0.15) follow its direction, otherwise stay flat.",
       n=120, level=0.15)
def g04(df, n, level):
    c = df["close"]
    change = c - c.shift(n)
    er = change.abs() / c.diff().abs().rolling(n).sum()
    return ls((er > level) & (change > 0), (er > level) & (change < 0))


@strat("Choppiness-index regime", REG,
       "Choppiness index(84) below 50 marks a trending market: follow the 14-day return; flat when choppy.",
       n=84, level=50)
def g05(df, n, level):
    c = df["close"]
    pc = c.shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    rng = df["high"].rolling(n).max() - df["low"].rolling(n).min()
    chop = 100 * np.log10(tr.rolling(n).sum() / rng) / np.log10(n)
    ret = c / c.shift(n) - 1
    return ls((chop < level) & (ret > 0), (chop < level) & (ret < 0))


@strat("Regime-sided breakouts", REG,
       "Rising 100-day SMA: only long 10-day breakouts. Falling: only short breakdowns. Exit on the 5-day opposite extreme.",
       regime_n=600, slope_n=60, n_in=60, n_out=30)
def g06(df, regime_n, slope_n, n_in, n_out):
    c = df["close"]
    m = sma(c, regime_n)
    bull, bear = m > m.shift(slope_n), m < m.shift(slope_n)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & bull, c < xl, (c < lo) & bear, c > xh)


@strat("Trend-quality (R-squared) regime", REG,
       "Follow the 30-day regression slope only when the fit is clean (R-squared > 0.4); flat in noisy markets.",
       n=180, r2=0.4)
def g07(df, n, r2):
    y = np.log(df["close"])
    x = pd.Series(np.arange(len(y), dtype=float), index=y.index)
    corr = y.rolling(n).corr(x)
    return ls((corr > 0) & (corr ** 2 > r2), (corr < 0) & (corr ** 2 > r2))


@strat("Volume-participation regime", REG,
       "Momentum vote traded only while 7-day average volume is above its 90-day average (moves backed by participation).",
       n1=90, n2=180, n3=360, vol_fast=42, vol_slow=540)
def g08(df, n1, n2, n3, vol_fast, vol_slow):
    v = mom_vote(df["close"], (n1, n2, n3))
    active = sma(df["volume"], vol_fast) > sma(df["volume"], vol_slow)
    return ls((v > 0) & active, (v < 0) & active)


@strat("Autocorrelation regime", REG,
       "Trade the momentum vote only while daily returns are positively autocorrelated over the last 60 days (trending regime).",
       n1=90, n2=180, n3=360, lag=6, window=360)
def g09(df, n1, n2, n3, lag, window):
    c = df["close"]
    r = c.pct_change(lag)
    ac = r.rolling(window).corr(r.shift(lag))
    v = mom_vote(c, (n1, n2, n3))
    return ls((v > 0) & (ac > 0), (v < 0) & (ac > 0))


@strat("Three-timeframe agreement", REG,
       "Weekly (42-bar) and monthly (180-bar) returns and the 100-day SMA side must all agree; otherwise flat.",
       fast=42, mid=180, slow=600)
def g10(df, fast, mid, slow):
    c = df["close"]
    a = c / c.shift(fast) - 1
    b = c / c.shift(mid) - 1
    m = sma(c, slow)
    return ls((a > 0) & (b > 0) & (c > m), (a < 0) & (b < 0) & (c < m))


@strat("Variance-ratio regime", REG,
       "When the 2-day/4-hour variance ratio over 60 days is above 1 (returns trend rather than revert) follow 30-day momentum; else flat.",
       q=12, window=360, n=180)
def g11(df, q, window, n):
    c = df["close"]
    vr = c.pct_change(q).rolling(window).var() / (q * c.pct_change().rolling(window).var())
    ret = c / c.shift(n) - 1
    return ls((vr > 1) & (ret > 0), (vr > 1) & (ret < 0))


@strat("Market-structure regime", REG,
       "Higher high and higher low versus the previous 15-day block: long. Lower high and lower low: short. Mixed: flat.",
       n=90)
def g12(df, n):
    hh = df["high"].rolling(n).max()
    ll = df["low"].rolling(n).min()
    return ls((hh > hh.shift(n)) & (ll > ll.shift(n)), (hh < hh.shift(n)) & (ll < ll.shift(n)))


@strat("Extension-capped trend", REG,
       "Momentum vote, but stand aside when price is stretched more than 8 ATR from SMA300 (late, crowded trend).",
       n1=90, n2=180, n3=360, ma_n=300, atr_n=42, cap=8.0)
def g13(df, n1, n2, n3, ma_n, atr_n, cap):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    ok = (c - sma(c, ma_n)).abs() < cap * atr(df, atr_n)
    return ls((v > 0) & ok, (v < 0) & ok)


@strat("Asymmetric-evidence momentum", REG,
       "Long on a simple majority of the 30/60/90-day returns, but short only when all three are negative (shorts need stronger evidence).",
       n1=180, n2=360, n3=540)
def g14(df, n1, n2, n3):
    spans = (n1, n2, n3)
    v = mom_vote(df["close"], spans)
    return ls(v > 0, v <= -len(spans))


# ----------------------------------------------------------------------------- combinations


@strat("Three-system majority", COMBO,
       "Majority of three different trend definitions: EMA 50/200, 30-day momentum and the Donchian 20d/10d state.",
       fast=50, slow=200, mom_n=180, n_in=120, n_out=60)
def c01(df, fast, slow, mom_n, n_in, n_out):
    c = df["close"]
    s = (np.sign(ema(c, fast) - ema(c, slow)) + np.sign(c / c.shift(mom_n) - 1).fillna(0)
         + donchian(df, n_in, n_out))
    return ls(s >= 2, s <= -2)


@strat("Trend with pullback-or-breakout entries", COMBO,
       "In a voted uptrend enter on either an RSI(4) dip or a 40-bar breakout; exit on a 40-bar low or trend flip; mirrored short.",
       n1=90, n2=180, n3=360, rsi_n=4, low=25, n_brk=40)
def c02(df, n1, n2, n3, rsi_n, low, n_brk):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    x = rsi(c, rsi_n)
    hi = df["high"].rolling(n_brk).max().shift(1)
    lo = df["low"].rolling(n_brk).min().shift(1)
    up, dn = v > 0, v < 0
    return latch(up & ((x < low) | (c > hi)), (c < lo) | ~up, dn & ((x > 100 - low) | (c < lo)), (c > hi) | ~dn)


@strat("SMA side plus MACD timing", COMBO,
       "Long when price is above SMA300 and the 24/52 MACD line is positive; short on the mirror; flat when they disagree.",
       ma_n=300, fast=24, slow=52)
def c03(df, ma_n, fast, slow):
    c = df["close"]
    m = sma(c, ma_n)
    macd = ema(c, fast) - ema(c, slow)
    return ls((c > m) & (macd > 0), (c < m) & (macd < 0))


@strat("Keltner breakout with 60d momentum", COMBO,
       "Keltner 50/2 breakout state, kept only when it agrees with the sign of the 60-day return.",
       n=50, k=2.0, mom_n=360)
def c04(df, n, k, mom_n):
    c = df["close"]
    state = keltner(df, n, k)
    ret = c / c.shift(mom_n) - 1
    return ls((state > 0) & (ret > 0), (state < 0) & (ret < 0))


@strat("Momentum vote with OBV confirmation", COMBO,
       "30/60/90-day momentum vote, kept only when on-balance volume is on the same side of its 400-bar average.",
       n1=180, n2=360, n3=540, obv_n=400)
def c05(df, n1, n2, n3, obv_n):
    v = mom_vote(df["close"], (n1, n2, n3))
    o = obv(df)
    m = sma(o, obv_n)
    return ls((v > 0) & (o > m), (v < 0) & (o < m))


@strat("Momentum vote with vol-rank kill switch", COMBO,
       "Momentum vote, flat whenever 7-day realised vol is in the top decile of the last 90 days.",
       n1=90, n2=180, n3=360, vol_n=42, window=540, cap=0.9)
def c06(df, n1, n2, n3, vol_n, window, cap):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    ok = c.pct_change().rolling(vol_n).std().rolling(window).rank(pct=True) < cap
    return ls((v > 0) & ok, (v < 0) & ok)


@strat("Six-horizon momentum score with hysteresis", COMBO,
       "Net count of six return horizons (10 to 80 days): enter at a 4-to-2 majority, hold until the score crosses zero.",
       n1=60, n2=120, n3=180, n4=240, n5=360, n6=480, enter=2)
def c07(df, n1, n2, n3, n4, n5, n6, enter):
    c = df["close"]
    spans = (n1, n2, n3, n4, n5, n6)
    v = mom_vote(c, spans).where(c.shift(max(spans)).notna())
    return latch(v >= enter, v <= 0, v <= -enter, v >= 0)


@strat("Momentum vote with adverse-shock pause", COMBO,
       "Momentum vote, but step aside for 2 days after a 12-hour move of more than 3 sigma against the position.",
       n1=90, n2=180, n3=360, k_bars=3, k=3.0, pause=12, vol_n=180)
def c08(df, n1, n2, n3, k_bars, k, pause, vol_n):
    c = df["close"]
    v = np.sign(mom_vote(c, (n1, n2, n3))).where(c.shift(max(n1, n2, n3)).notna(), 0)
    z = (c / c.shift(k_bars) - 1) / (c.pct_change().rolling(vol_n).std().shift(1) * k_bars ** 0.5)
    adverse = ((v > 0) & (z < -k)) | ((v < 0) & (z > k))
    paused = adverse.astype(float).rolling(pause).max() > 0
    return v.where(~paused, 0)


@strat("Five-signal cross-family vote", COMBO,
       "EMA cross, 30d momentum, Donchian state, OBV trend and Keltner state: trade when at least four of five agree.",
       fast=50, slow=200, mom_n=180, n_in=120, n_out=60, obv_n=400, kel_n=100, kel_k=3.0, need=3)
def c09(df, fast, slow, mom_n, n_in, n_out, obv_n, kel_n, kel_k, need):
    c = df["close"]
    o = obv(df)
    s = (np.sign(ema(c, fast) - ema(c, slow)) + np.sign(c / c.shift(mom_n) - 1).fillna(0)
         + donchian(df, n_in, n_out) + np.sign(o - sma(o, obv_n)).fillna(0) + keltner(df, kel_n, kel_k))
    return ls(s >= need, s <= -need)


@strat("Pullback entry with trailing exit", COMBO,
       "In a voted uptrend buy an RSI(14) < 45 dip and ride it with a 4-ATR trailing stop; mirrored short.",
       n1=90, n2=180, n3=360, rsi_n=14, low=45, atr_n=42, mult=4.0)
def c10(df, n1, n2, n3, rsi_n, low, atr_n, mult):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    x = rsi(c, rsi_n)
    return trail((v > 0) & (x < low), (v < 0) & (x > 100 - low), c, atr(df, atr_n), mult)


@strat("Strict confluence", COMBO,
       "Momentum vote, SMA300 side and ADX(14) > 15 must all line up; flat otherwise.",
       n1=90, n2=180, n3=360, ma_n=300, adx_n=14, level=15)
def c11(df, n1, n2, n3, ma_n, adx_n, level):
    c = df["close"]
    v = mom_vote(c, (n1, n2, n3))
    m = sma(c, ma_n)
    on = dmi(df, adx_n)[2] > level
    return ls((v > 0) & (c > m) & on, (v < 0) & (c < m) & on)


@strat("Breakout plus momentum plus volume", COMBO,
       "40-bar breakout in the direction of 30-day momentum on above-average volume; exit on the 20-bar opposite extreme or a momentum flip.",
       n_in=40, n_out=20, mom_n=180, vol_n=120, vol_mult=1.2)
def c12(df, n_in, n_out, mom_n, vol_n, vol_mult):
    c = df["close"]
    up, dn = c > c.shift(mom_n), c < c.shift(mom_n)
    big = df["volume"] > vol_mult * sma(df["volume"], vol_n).shift(1)
    hi = df["high"].rolling(n_in).max().shift(1)
    lo = df["low"].rolling(n_in).min().shift(1)
    xh = df["high"].rolling(n_out).max().shift(1)
    xl = df["low"].rolling(n_out).min().shift(1)
    return latch((c > hi) & up & big, (c < xl) | ~up, (c < lo) & dn & big, (c > xh) | ~dn)


@strat("Slow EMA with fast Keltner agreement", COMBO,
       "Position only when the EMA 50/200 direction and the fast Keltner 20/2 breakout state point the same way.",
       fast=50, slow=200, kel_n=20, kel_k=2.0)
def c13(df, fast, slow, kel_n, kel_k):
    c = df["close"]
    d = np.sign(ema(c, fast) - ema(c, slow))
    state = keltner(df, kel_n, kel_k)
    return ls((d > 0) & (state > 0), (d < 0) & (state < 0))


@strat("Seven-signal diversified average", COMBO,
       "Average of seven trend/momentum/breakout/volume signals; long above +0.3, short below -0.3, flat in between.",
       fast=50, slow=200, ma_n=300, mom1=180, mom2=360, n_in=120, n_out=60, kel_n=100, kel_k=3.0, obv_n=400, level=0.3)
def c14(df, fast, slow, ma_n, mom1, mom2, n_in, n_out, kel_n, kel_k, obv_n, level):
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
