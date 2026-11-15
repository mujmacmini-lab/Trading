"""Research harness used to build the strategy set (not needed to run backtest.py).

    python research/lab.py strategies/s001.py [more files...]   robustness report per file
    python research/lab.py --all [--valid]                      one line per strategy

Robustness views (all with the engine's own simulate(), so costs are identical):
  * design period (to 2023-12-31) vs internal validation (2024-01 -> end of in-sample)
  * Sharpe per calendar year, long leg and short leg separately
  * Sharpe with costs doubled
  * parameter jitter: every numeric parameter x0.7 and x1.4, one at a time
"""
import glob
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd

import backtest as bt

DESIGN_END = "2023-12-31"
ANN = np.sqrt(bt.BARS_PER_YEAR)


def sharpe(x):
    sd = x.std()
    return float(x.mean() / sd * ANN) if sd > 0 else 0.0


def run(mod, params, df, cost_mult=1.0):
    sig = bt.clean_signal(mod.signal(df.copy(), **params), df.index)
    net, pos, trades = bt.simulate(df, sig, cost_mult)
    return sig, net, pos, trades


def jitter_params(params):
    out = []
    for k, v in params.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        for m in (0.7, 1.4):
            nv = v * m
            if isinstance(v, int):
                nv = max(1, int(round(nv)))
                if nv == v:
                    continue
            p = dict(params)
            p[k] = nv
            out.append((f"{k}={nv:g}", p))
    return out


def report(path, df, valid=False, jitter=True):
    mod, params = bt.load_strategy(path)
    sig, net, pos, trades = run(mod, params, df)
    r = df["close"].pct_change().fillna(0)
    d = net.loc[:DESIGN_END]
    v = net.loc[DESIGN_END:]
    res = {
        "file": os.path.basename(path)[:-3],
        "fam": getattr(mod, "FAMILY", "")[:5],
        "tr": len(trades),
        "tr_d": int((trades["entry"] <= pd.Timestamp(DESIGN_END, tz="UTC")).sum()) if len(trades) else 0,
        "exp": round(float((pos != 0).mean()), 2),
        "sh_d": round(sharpe(d), 2),
    }
    years = sorted(set(net.index.year))
    for y in years:
        if y > 2023 and not valid:
            continue
        res[f"y{y % 100}"] = round(sharpe(net[net.index.year == y]), 2)
    # legs (gross of the other leg, costs attributed to whole)
    dl = (pos.clip(lower=0) * r).loc[:DESIGN_END] if not valid else pos.clip(lower=0) * r
    ds = (pos.clip(upper=0) * r).loc[:DESIGN_END] if not valid else pos.clip(upper=0) * r
    res["L"] = round(sharpe(dl), 2)
    res["S"] = round(sharpe(ds), 2)
    _, net2, _, _ = run(mod, params, df, cost_mult=2.0)
    res["c2x"] = round(sharpe(net2.loc[:DESIGN_END] if not valid else net2), 2)
    if jitter:
        js = []
        for _, p in jitter_params(params):
            try:
                _, nj, _, _ = run(mod, p, df)
                js.append(sharpe(nj.loc[:DESIGN_END] if not valid else nj))
            except Exception:
                js.append(np.nan)
        if js:
            res["j_min"] = round(float(np.nanmin(js)), 2)
            res["j_med"] = round(float(np.nanmedian(js)), 2)
    if valid:
        res["sh_v"] = round(sharpe(v), 2)
        res["sh_all"] = round(sharpe(net), 2)
        eq = (1 + net).cumprod()
        res["mdd"] = round(float((eq / eq.cummax() - 1).min()), 2)
    return res


def main(argv):
    df = bt.load_data()
    valid = "--valid" in argv
    nojit = "--nojit" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    if "--all" in argv:
        args = sorted(glob.glob(os.path.join(ROOT, "strategies", "s*.py")))
    rows = []
    for p in args:
        try:
            rows.append(report(p, df, valid=valid, jitter=not nojit))
        except Exception as e:
            rows.append({"file": os.path.basename(p)[:-3], "fam": f"ERR {type(e).__name__}: {e}"})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main(sys.argv)
