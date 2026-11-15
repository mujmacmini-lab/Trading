# FINAL — BTCUSDT 4h strategy set

100 strategies, `strategies/s001.py` … `s100.py`, all `OK` in `python backtest.py --all`
(no look-ahead, 37–552 trades each). Families: trend following 16, momentum 16, breakout 16,
volatility 14, regime filter 14, combination 14, mean reversion 10.

## What I expect out of sample

Not the in-sample numbers. I held back 2024-01 → 2025-10 while designing the first version of the
set on 2020-04 → 2023-12, then scored it once:

| first version of the set (100 strategies)       | design ≤2023 | held-back 2024–25 |
|--------------------------------------------------|-------------:|------------------:|
| median Sharpe                                    | 0.94         | −0.11             |
| share with positive Sharpe                       | 100%         | 38%               |
| rank correlation of design Sharpe with held-back | —            | +0.10             |

So a good backtest Sharpe predicted almost nothing, and 2025 in particular was hostile to nearly
every trend and breakout rule (buy-and-hold Sharpe over the same window: 1.32). After that test
there is no untouched data left: the final set and the picks below were chosen with all of the
in-sample data in view. For the top 5 I would plan on a Sharpe of roughly 0.3–0.6, not 1.0, with
drawdowns of 30–50% (positions are always 1x, unlevered).

## Top 5

In-sample figures from `backtest.py` (net of 0.075% per side). "Yearly Sharpe" is 2020 … 2025.

| # | id | strategy | Sharpe | net return | max DD | trades | yearly Sharpe |
|---|----|----------|-------:|-----------:|-------:|-------:|---------------|
| 1 | **s020** | Momentum vote 30/60/90/120d | 1.06 | +1064% | −53% | 182 | 3.26 / 0.86 / 0.64 / 1.44 / 0.86 / 0.10 |
| 2 | s018 | Time-series momentum 60d | 1.04 | +1058% | −57% | 187 | 2.71 / 1.47 / 0.45 / 1.50 / 0.45 / 0.17 |
| 3 | s073 | ADX-gated momentum vote | 1.26 | +1746% | −48% | 355 | 3.39 / 1.36 / 0.77 / 1.63 / 0.83 / 0.19 |
| 4 | s035 | Trend-filtered fast Donchian | 1.07 | +698% | −41% | 197 | 2.52 / 0.90 / 0.50 / 2.21 / 1.19 / −0.34 |
| 5 | s042 | Keltner 20/2 in voted trend | 0.97 | +363% | −32% | 171 | 1.92 / 0.71 / 0.88 / 1.66 / 1.26 / −0.44 |

Why each one:

1. **s020 — Momentum vote 30/60/90/120d.** Signs of the 1-, 2-, 3- and 4-month returns vote; flat on
   a 2–2 tie. Four lookbacks on a plain monthly grid, no thresholds, so there is very little to fit.
   Single lookbacks between 40 and 100 days score anywhere from 0.46 to 1.04 depending on the exact
   number; the vote averages that noise out and still gets 1.06. Positive in all six calendar years
   and in 10 of 12 half-years, long and short both allowed, made money in the 2022 bear market.
   Stress: Sharpe 0.89 at triple costs, 1.00 with entries delayed one bar, 0.79 at worst when any
   lookback is halved or doubled, 0.77 excluding 2020.
2. **s018 — Time-series momentum 60d.** One parameter. It was in the first version of the set, so
   its held-back result (Sharpe 0.33, both 2024 and 2025 positive) is a genuine out-of-sample
   observation, and it is positive in all six calendar years. Ranked below s020 because 60 days sits on a local peak (halving or doubling it
   drops Sharpe to 0.60).
3. **s073 — ADX-gated momentum vote.** 30/60/90-day vote, traded only while ADX(14) > 20, so it sits
   out when nothing is moving. Best stress profile of the set (worst half-year −0.21, all years
   positive, 0.79 at worst under wide parameter changes). Ranked third because it has two more
   parameters, twice the turnover (Sharpe falls to 0.90 at triple costs), and was built after the
   held-back test.
4. **s035 — Trend-filtered fast Donchian.** 20-bar breakouts taken only on the trend side of the
   50-day SMA, exit on the 10-bar opposite extreme. In the market half the time. In the first version
   of the set and positive on the held-back period (Sharpe 0.56). Correlation with s020 is 0.52, so it
   is a partly different bet.
5. **s042 — Keltner 20/2 in voted trend.** ATR-channel breakouts in the direction of the slow vote;
   in the market 26% of the time, smallest drawdown of the five, short side contributes (2022: +30%).
   Adding a slow-trend direction filter improved all 23 breakout-type rules I tried it on, which is
   why I trust the filter; the rule itself was built after the held-back test.

## Champion: s020 — Momentum vote 30/60/90/120d

**Biggest risk: a sideways, whipsawing market.** The rule needs moves that persist for a month or
more. In a range where the 1–4 month returns keep flipping sign it pays costs and gives back gains
with nothing to offset them; that is what 2025 looked like in-sample (−4% over January–October). It is also slow by design, so it hands back roughly a month of a move before it reverses
after a sharp V-turn, and the in-sample drawdown was −53%. A hidden period that is one long range
would most likely produce a small loss, not a profit.

Two smaller points: nearly half of its in-sample compounded return comes from 2020 (Sharpe 0.77
without that year),
and it averages about 33 trades a year, so if the hidden test also requires 30 trades it is
borderline on a window shorter than a year.

## Tried and abandoned

| idea | what happened | verdict |
|------|---------------|---------|
| Plain mean reversion: RSI(2/4/7/14) extremes, Bollinger fades, down-streak fades | Sharpe −0.2 to −2.1 after costs, negative in most years | BTC 4h trends at these horizons; fading it pays the spread to lose |
| Short-term reversal over 1–12 bars | −0.7 to −2.0 | cost-dominated (up to 4,500 trades) |
| Fast momentum, lookback of 1–4 days | −0.4 to −1.4 | cost-dominated |
| Fading in low-ADX "range" regimes | −0.3 to −0.8 | the range filter does not rescue mean reversion |
| Shorting over-extension (price k ATR above its average) | −0.8 to −1.4 | strong moves continued |
| Range-expansion bar continuation | negative for 10 of 12 settings (−1.0 to +0.3) | no edge |
| "Fresh trend" regime (trade only the first 10 days after the vote flips) | 1.82 in design, −0.58 held back | found by data mining, failed the first honest test; removed |
| Pullback buys with a 30-day trend filter | about 1.0 at exactly 180 bars, 0.2–0.4 at 120 or 240 | a parameter island; two weak versions kept as family representatives, the rest replaced |
| KAMA, Connors RSI(2) long-only, close-vs-range volatility ratio, new-high time stop, proximity to 60-day extreme, breakout + OBV | Sharpe −0.3 to 0.3 | replaced by slower designs |
| Hour-of-day / day-of-week seasonality | not built | daily turnover at 0.15% per round trip needs an edge far larger than anything in the data |
| Long-only trend rules in the top 5 | the two best have in-sample Sharpe 1.1–1.4 but −1.9 and −2.3 in 2022 | they are mostly a bet that BTC keeps drifting up; kept in the set (s015, s063, s068, s056), kept out of the picks |

What did hold up, and shaped the final set: horizons of 30 days and longer, votes across several
lookbacks instead of one, a flat state when signals disagree, and taking breakouts only with the
slow trend.

## Caveats you should know about

- **Weak tail.** Raw breakouts (s033, s036–s038, s044, s045, s047) lost heavily in 2025 at every
  speed, and the mean-reversion family (s049–s058) is thin: its median in-sample Sharpe is 0.62 and
  most of it is trend exposure entered on a dip. They are honest representatives of their families,
  not strategies I would trade.
- **Correlation.** The top three are close to the same bet (pairwise correlation 0.83–0.90). If slow
  momentum fails in the hidden period they fail together; s035 and s042 are the partial hedge.
- **Significance.** Sharpe 1.06 over 5.6 years is a t-statistic of about 2.5 before allowing for the
  hundred-plus variants I looked at. That is suggestive, not proof.
- **Warm-up.** The picks need 30–120 days of history. If the hidden data is scored on its own rather
  than appended to the in-sample file, s020 starts trading after 30 days and reaches full strength
  after 120.
- **What I knew.** My training data runs past October 2025, so I have a rough idea of how BTC moved
  afterwards. I did not use it: the selection rule (long/short symmetric, positive in the 2022 bear
  market and in 2025) was fixed from the in-sample data, and no strategy was tilted long or short on
  that knowledge. The repository also contains a `hidden/` folder next to this one; I saw its file
  name in a directory listing and never opened it.

## Reproducing

`research/` holds the harness: `specs_a.py` / `specs_b.py` are the single source for all 100
strategies, `build.py` writes `strategies/*.py` and `strategies/index.csv` from them, `lab.py`
gives per-year, cost and parameter-jitter views, `holdout.py` the design-versus-held-back table
(`holdout.csv`), and `stress.py` the stress tests quoted above.
