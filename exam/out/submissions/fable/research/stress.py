"""Stress tests for shortlisted strategies: half-year blocks, cost multiples, one-bar entry delay,
wide parameter jitter (x0.5 .. x2) and a cold start on the last two years only.

    python research/stress.py s020 s018 ...
"""
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import lab, backtest as bt

df = bt.load_data()
rows = []
for sid in sys.argv[1:]:
    mod, params = bt.load_strategy(os.path.join(lab.ROOT, "strategies", sid + ".py"))
    sig, net, pos, trades = lab.run(mod, params, df)
    half = net.groupby([net.index.year, (net.index.month - 1) // 6]).apply(lab.sharpe)
    costs = [lab.sharpe(lab.run(mod, params, df, m)[1]) for m in (2, 3)]
    late = bt.simulate(df, sig.shift(1).fillna(0))[0]
    wide = []
    for k, v in params.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        for m in (0.5, 0.75, 1.5, 2.0):
            nv = max(1, int(round(v * m))) if isinstance(v, int) else v * m
            try:
                wide.append(lab.sharpe(lab.run(mod, {**params, k: nv}, df)[1]))
            except Exception:
                pass
    cold_df = df.loc["2023-11-01":]
    cold = bt.simulate(cold_df, bt.clean_signal(mod.signal(cold_df.copy(), **params), cold_df.index))[0]
    eq = (1 + net).cumprod()
    ex20 = net.loc["2021-01-01":]
    rows.append(dict(
        id=sid, name=mod.NAME[:30], tr=len(trades), sh=lab.sharpe(net), sh_ex2020=lab.sharpe(ex20),
        halves_pos=f"{int((half > 0).sum())}/{len(half)}", worst_half=half.min(),
        c2x=costs[0], c3x=costs[1], delay1=lab.sharpe(late),
        wide_min=min(wide) if wide else np.nan, wide_med=float(np.median(wide)) if wide else np.nan,
        cold_2y=lab.sharpe(cold.loc["2024-01-01":]), warm_2y=lab.sharpe(net.loc["2024-01-01":]),
        mdd=float((eq / eq.cummax() - 1).min()), ret_pct=float(eq.iloc[-1] - 1) * 100,
    ))
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(2).to_string(index=False))
