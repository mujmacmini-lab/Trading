"""Internal out-of-sample check: design period (<=2023) statistics vs validation (2024-01 -> 2025-10)."""
import glob, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import lab, backtest as bt

df = bt.load_data()
rows = []
for p in sorted(glob.glob(os.path.join(lab.ROOT, "strategies", "s*.py"))):
    mod, params = bt.load_strategy(p)
    sig, net, pos, trades = lab.run(mod, params, df)
    d, v = net.loc[:lab.DESIGN_END], net.loc["2024-01-01":]
    yrs = {y: lab.sharpe(net[net.index.year == y]) for y in range(2020, 2026)}
    js = []
    for _, pj in lab.jitter_params(params):
        _, nj, _, _ = lab.run(mod, pj, df)
        js.append((lab.sharpe(nj.loc[:lab.DESIGN_END]), lab.sharpe(nj.loc["2024-01-01":]), lab.sharpe(nj)))
    js = np.array(js) if js else np.zeros((1, 3))
    _, n2, _, _ = lab.run(mod, params, df, 2.0)
    r = df["close"].pct_change().fillna(0)
    tv = trades[trades["entry"] >= pd.Timestamp("2024-01-01", tz="UTC")]
    rows.append(dict(
        id=os.path.basename(p)[:-3], fam=mod.FAMILY[:6], name=mod.NAME[:34], tr=len(trades), tr_v=len(tv),
        exp=round(float((pos != 0).mean()), 2),
        sh_d=lab.sharpe(d), jmin_d=js[:, 0].min(), jmed_d=np.median(js[:, 0]),
        miny_d=min(yrs[y] for y in (2021, 2022, 2023)), S_d=lab.sharpe((pos.clip(upper=0) * r).loc[:lab.DESIGN_END]),
        sh_v=lab.sharpe(v), y24=yrs[2024], y25=yrs[2025], jmed_v=np.median(js[:, 1]),
        sh_all=lab.sharpe(net), c2x_all=lab.sharpe(n2), jmin_all=js[:, 2].min(), jmed_all=np.median(js[:, 2]),
        miny_all=min(yrs.values()), ret_v=float((1 + v).prod() - 1),
    ))
out = pd.DataFrame(rows).round(2)
out.to_csv(os.path.join(lab.HERE, "holdout.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
print(out.drop(columns=["name"]).to_string(index=False))
print("\nbuy&hold validation sharpe:", round(lab.sharpe(r.loc["2024-01-01":]), 2))
print("share positive in validation:", (out.sh_v > 0).mean(), " median sh_v:", out.sh_v.median(), " median sh_d:", out.sh_d.median())
print("\nSpearman rank correlation of design-period statistics with validation Sharpe:")
for k in ("sh_d", "jmin_d", "jmed_d", "miny_d", "S_d", "exp", "tr"):
    print(f"  {k:8s} {out[k].rank().corr(out.sh_v.rank()):+.2f}")
print("\nby family (median):")
print(out.groupby("fam")[["sh_d", "sh_v", "y24", "y25"]].median().round(2))
