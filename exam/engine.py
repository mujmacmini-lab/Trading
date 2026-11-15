"""STEP 2-4 - the scoring engine. Everything goes through fable/backtest.py (same fees, next-candle rule, metrics)."""
import glob
import importlib.util
import os
import re
import sys

sys.dont_write_bytecode = True

import numpy as np
import pandas as pd

CUT = pd.Timestamp("2025-11-01 00:00", tz="UTC")  # hidden period = ts >= CUT


def load_engine(root):
    spec = importlib.util.spec_from_file_location("backtest", os.path.join(root, "fable", "backtest.py"))
    bt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bt)
    return bt


def run(bt, path, full, overrides=None, cost_mult=1.0, check=False):
    """Run one strategy file on the FULL data. Returns net, pos, trades and the look-ahead verdict."""
    mod, params = bt.load_strategy(path)
    params.update(overrides or {})
    sig = bt.clean_signal(mod.signal(full.copy(), **params), full.index)
    problem = bt.lookahead_check(mod, params, full, sig) if check else None
    net, pos, trades = bt.simulate(full, sig, cost_mult=cost_mult)
    return {"net": net, "pos": pos, "trades": trades, "lookahead": problem, "params": params}


def split(bt, res, close):
    """(in-sample metrics, hidden metrics, hidden trades). Trades are counted by entry time."""
    net, pos, trades = res["net"], res["pos"], res["trades"]
    h = net.index >= CUT
    ins = bt.metrics(net[~h], pos[~h], trades[trades["entry"] < CUT], close[~h])
    hid_trades = trades[trades["entry"] >= CUT].reset_index(drop=True)
    hid = bt.metrics(net[h], pos[h], hid_trades, close[h])
    return ins, hid, hid_trades


def champion_id(final_md):
    """The first sNNN after the word 'champion' in FINAL.md."""
    text = open(final_md, encoding="utf-8").read()
    m = re.search(r"champion", text, re.I)
    m = re.search(r"s\d{3}", text[m.end():]) if m else None
    return m.group(0) if m else None


def spearman(a, b):
    return float(pd.Series(a).rank().corr(pd.Series(b).rank()))


def score_ai(bt, folder, full, insample):
    """Gate every strategy on in-sample data, then score the OK ones on the full data."""
    close = full["close"]
    rows, runs = [], {}
    for path in sorted(glob.glob(os.path.join(folder, "strategies", "s*.py"))):
        sid = os.path.basename(path)[:-3]
        gate = bt.evaluate(path, insample)  # the AI's own exam conditions: in-sample data only
        row = {"id": sid, "name": gate["name"], "family": gate["family"], "gate": gate["status"],
               "gate_reason": gate["reason"], "scored": False}
        if gate["status"] == "OK":
            try:
                res = run(bt, path, full, check=True)
                if res["lookahead"]:
                    row["gate_reason"] = "full data: " + res["lookahead"]
                else:
                    ins, hid, hid_trades = split(bt, res, close)
                    row.update({"scored": True})
                    row.update({f"is_{k}": v for k, v in ins.items()})
                    row.update({f"hid_{k}": v for k, v in hid.items()})
                    runs[sid] = {**res, "hid_trades": hid_trades, "path": path}
            except Exception as e:
                row["gate_reason"] = f"full data: {type(e).__name__}: {e}"
        rows.append(row)
    table = pd.DataFrame(rows)
    if len(table) and table["scored"].any():
        s = table["scored"]
        table.loc[s, "is_rank"] = table.loc[s, "is_sharpe"].rank(ascending=False, method="min")
        table.loc[s, "hid_rank"] = table.loc[s, "hid_sharpe"].rank(ascending=False, method="min")
    return table, runs


# ---- the 5 tests -------------------------------------------------------------------------------

def test1_new_data(table, champ):
    t = table[table["scored"]]
    bh = float(t["hid_buy_hold_pct"].iloc[0])
    c = t[t["id"] == champ].iloc[0]
    return {
        "scored": int(len(t)), "submitted": int(len(table)),
        "profitable": int((t["hid_net_return_pct"] > 0).sum()),
        "beat_buy_hold": int((t["hid_net_return_pct"] > bh).sum()),
        "buy_hold_pct": bh,
        "median_is_sharpe": round(float(t["is_sharpe"].median()), 2),
        "median_hid_sharpe": round(float(t["hid_sharpe"].median()), 2),
        "spearman": round(spearman(t["is_sharpe"], t["hid_sharpe"]), 2),
        "champ_is_cagr_pct": float(c["is_cagr_pct"]), "champ_is_sharpe": float(c["is_sharpe"]),
        "champ_hid_return_pct": float(c["hid_net_return_pct"]), "champ_hid_sharpe": float(c["hid_sharpe"]),
        "champ_hid_max_dd_pct": float(c["hid_max_drawdown_pct"]), "champ_hid_trades": int(c["hid_trades"]),
        "champ_hid_rank": int(c["hid_rank"]), "champ_is_rank": int(c["is_rank"]),
    }


def test2_tweaks(bt, path, full):
    """Each numeric PARAM x0.8 and x1.2, one at a time (ints rounded, unchanged values skipped)."""
    _, params = bt.load_strategy(path)
    rows = []
    for key, val in params.items():
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        for mult in (0.8, 1.2):
            new = int(round(val * mult)) if isinstance(val, int) else val * mult
            if new == val:
                continue
            try:
                _, hid, _ = split(bt, run(bt, path, full, overrides={key: new}), full["close"])
                rows.append({"param": key, "from": val, "to": new, "mult": mult,
                             "hid_return_pct": hid["net_return_pct"], "hid_sharpe": hid["sharpe"]})
            except Exception as e:
                rows.append({"param": key, "from": val, "to": new, "mult": mult,
                             "hid_return_pct": float("nan"), "hid_sharpe": float("nan"), "error": str(e)})
    t = pd.DataFrame(rows)
    return t, int((t["hid_return_pct"] > 0).sum()) if len(t) else 0


def test3_fees(bt, path, full):
    out = {}
    for mult in (0, 1, 2, 3):
        _, hid, _ = split(bt, run(bt, path, full, cost_mult=float(mult)), full["close"])
        out[mult] = hid["net_return_pct"]
    return out


def test4_worst_case(trade_rets, n_samples=1000, seed=42):
    """Resample the champion's hidden trades with replacement and compound each resample."""
    rets = np.asarray(trade_rets, dtype=float)
    if len(rets) == 0:
        return None
    rng = np.random.default_rng(seed)
    finals, dds = [], []
    for _ in range(n_samples):
        eq = np.concatenate([[1.0], np.cumprod(1 + rng.choice(rets, size=len(rets), replace=True))])
        finals.append(eq[-1] - 1)
        dds.append((eq / np.maximum.accumulate(eq) - 1).min())
    finals, dds = np.array(finals), np.array(dds)
    return {"trades": int(len(rets)), "pct_below_zero": round(float((finals < 0).mean() * 100), 1),
            "median_max_dd_pct": round(float(np.median(dds) * 100), 2),
            "p5_max_dd_pct": round(float(np.percentile(dds, 5) * 100), 2),
            "median_final_pct": round(float(np.median(finals) * 100), 2)}


def test5_luck(bt, runs, full, n_twins=1000, seed=42):
    """% of random-entry twins each strategy's real hidden trades beat. One generator per AI, ids in order."""
    close_h = full["close"][full.index >= CUT]
    r = close_h.pct_change().to_numpy()  # r[0] is NaN; starts are drawn from 1 so it is never used
    n = len(r)
    cum = {1: np.concatenate([[0.0], np.nancumsum(np.log1p(r))]),      # cum[s][i] = sum of log(1 + side*r) over r[:i]
           -1: np.concatenate([[0.0], np.nancumsum(np.log1p(-r))])}
    cost = 2 * np.log(1 - bt.COST_PER_SIDE)
    rng = np.random.default_rng(seed)
    out = {}
    for sid in sorted(runs):
        trades = runs[sid]["hid_trades"]
        if len(trades) == 0:
            out[sid] = float("nan")
            continue
        real = float(np.log1p(trades["ret"]).sum())
        twins = np.zeros(n_twins)
        for side, bars in zip(trades["side"], trades["bars"]):
            L = int(min(bars, n - 2))
            s = rng.integers(1, n - L, size=n_twins)
            twins += cum[int(side)][s + L] - cum[int(side)][s] + cost   # log(prod(1 + side*r[s:s+L]) * (1-c)^2)
        out[sid] = round(float((real > twins).mean() * 100), 1)
    return out


def should_have_picked(table, min_trades=5):
    t = table[table["scored"] & (table["hid_trades"] >= min_trades)]
    if not len(t):
        return None
    b = t.sort_values("hid_sharpe", ascending=False).iloc[0]
    return {"id": b["id"], "name": b["name"], "family": b["family"], "hid_sharpe": float(b["hid_sharpe"]),
            "hid_return_pct": float(b["hid_net_return_pct"]), "hid_max_dd_pct": float(b["hid_max_drawdown_pct"]),
            "hid_trades": int(b["hid_trades"]), "is_rank": int(b["is_rank"]), "is_sharpe": float(b["is_sharpe"]),
            "of": int(table["scored"].sum())}


# ---- STEP 4: proof check ---------------------------------------------------------------------

PROOF = '''
import numpy as np
import pandas as pd

def rule_a(df):
    """Long when the sum of the signs of the 90-, 180- and 360-candle returns is above zero, otherwise flat."""
    close = df["close"]
    votes = sum(np.sign(close.pct_change(n)).fillna(0) for n in (90, 180, 360))
    return (votes > 0).astype(int)

def rule_b(df):
    """EMA200 band: long above EMA*1.01, short below EMA*0.99, otherwise hold the previous position."""
    close = df["close"]
    ema = close.ewm(span=200, adjust=False).mean()
    raw = pd.Series(np.nan, index=df.index)
    raw[close > ema * 1.01] = 1.0
    raw[close < ema * 0.99] = -1.0
    return raw.ffill().fillna(0)
'''


def rule_b_near_miss(bt, full):
    """Diagnostic for a Rule B mismatch: the hidden-period bar that came closest to a band without
    crossing it, and what Rule B would have scored if that single bar had crossed."""
    ns = {}
    exec(PROOF, ns)
    close = full["close"]
    ema = close.ewm(span=200, adjust=False).mean()
    sig = bt.clean_signal(ns["rule_b"](full.copy()), full.index)
    h = full.index >= CUT
    gap_up = (close / (ema * 1.01) - 1).where((sig == -1) & h)   # short, close just under the long trigger
    gap_dn = (close / (ema * 0.99) - 1).where((sig == 1) & h)    # long, close just above the short trigger
    gaps = pd.concat([gap_up.abs(), gap_dn.abs()], axis=1).min(axis=1)
    t = gaps.idxmin()
    raw = pd.Series(np.nan, index=full.index)
    raw[close > ema * 1.01] = 1.0
    raw[close < ema * 0.99] = -1.0
    raw[t] = -sig[t]
    net, pos, trades = bt.simulate(full, raw.ffill().fillna(0))
    _, hid, _ = split(bt, {"net": net, "pos": pos, "trades": trades}, close)
    return {"bar": str(t), "close": float(close[t]), "gap_pct": round(float(gaps[t] * 100), 3),
            "gap_usd": round(float(gaps[t] * close[t]), 2),
            "if_crossed_return_pct": hid["net_return_pct"], "if_crossed_trades": hid["trades"]}


def proof_check(bt, full):
    ns = {}
    exec(PROOF, ns)
    close = full["close"]
    rows = []
    bh = None
    for label, fn, exp_ret, exp_tr in [("Rule A (momentum vote 90/180/360, long/flat)", ns["rule_a"], 8.07, 43),
                                       ("Rule B (EMA200 with 1% band, long/short)", ns["rule_b"], 26.15, 26)]:
        sig = bt.clean_signal(fn(full.copy()), full.index)
        net, pos, trades = bt.simulate(full, sig)
        _, hid, _ = split(bt, {"net": net, "pos": pos, "trades": trades}, close)
        bh = hid["buy_hold_pct"]
        rows.append((f"{label}: hidden return %", exp_ret, hid["net_return_pct"]))
        rows.append((f"{label}: hidden trades", exp_tr, hid["trades"]))
    rows.append(("Buy & hold over the hidden period %", -29.44, bh))
    return [(what, exp, got, "MATCH" if float(exp) == float(got) else "NO MATCH") for what, exp, got in rows]


# ---- the whole set as one equal-weight basket ---------------------------------------------------
# Not part of the original five-test spec: the same five questions asked of all strategies held together.

def basket_series(bt, runs, full, cost_mult=1.0):
    """Equal-weight basket, rebalanced every bar: (net, average position, average cost)."""
    r = full["close"].pct_change().fillna(0)
    pos = pd.DataFrame({sid: runs[sid]["pos"] for sid in sorted(runs)})
    turn = pos.diff().abs().fillna(pos.abs())
    P = pos.mean(axis=1)
    cost = turn.mean(axis=1) * bt.COST_PER_SIDE * cost_mult
    return P * r - cost, P, cost


def _hidden_stats(bt, net, P, close):
    h = net.index >= CUT
    empty = pd.DataFrame(columns=["entry", "exit", "side", "bars", "ret"])
    ins = bt.metrics(net[~h], P[~h], empty, close[~h])
    hid = bt.metrics(net[h], P[h], empty, close[h])
    keep = ("net_return_pct", "cagr_pct", "sharpe", "max_drawdown_pct", "buy_hold_pct")
    return {k: ins[k] for k in keep}, {k: hid[k] for k in keep}


def test_basket(bt, runs, full, n_samples=1000, seed=42):
    close = full["close"]
    h = full.index >= CUT
    net, P, cost = basket_series(bt, runs, full)
    ins, hid = _hidden_stats(bt, net, P, close)
    out = {"n": len(runs), "before": ins, "hidden": hid,
           "avg_position_hidden": round(float(P[h].mean()), 2),
           "median_pair_corr_hidden": None}
    nets = pd.DataFrame({sid: runs[sid]["net"][h] for sid in sorted(runs)})
    corr = nets.corr().to_numpy()
    out["median_pair_corr_hidden"] = round(float(np.nanmedian(corr[np.triu_indices(len(corr), 1)])), 2)

    # test 3 analogue: fees
    out["fees"] = {}
    for mult in (0, 1, 2, 3):
        n_m, P_m, _ = basket_series(bt, runs, full, cost_mult=float(mult))
        out["fees"][str(mult)] = _hidden_stats(bt, n_m, P_m, close)[1]["net_return_pct"]

    # test 2 analogue: every numeric setting of every strategy moved 20% down, then 20% up, all at once
    out["tweaks"] = []
    for mult in (0.8, 1.2):
        runs2, failed = {}, 0
        for sid in sorted(runs):
            _, params = bt.load_strategy(runs[sid]["path"])
            over = {}
            for k, v in params.items():
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                new = int(round(v * mult)) if isinstance(v, int) else v * mult
                if new != v:
                    over[k] = new
            try:
                runs2[sid] = run(bt, runs[sid]["path"], full, overrides=over)
            except Exception:
                runs2[sid] = runs[sid]
                failed += 1
        n2, P2, _ = basket_series(bt, runs2, full)
        hid2 = _hidden_stats(bt, n2, P2, close)[1]
        out["tweaks"].append({"mult": mult, "hid_return_pct": hid2["net_return_pct"], "hid_sharpe": hid2["sharpe"],
                              "kept_original": failed})

    # test 4 analogue: the basket has no single trades, so its hidden year is cut into weeks (42 candles)
    x = net[h].to_numpy()
    weeks = np.array([np.prod(1 + x[i:i + 42]) - 1 for i in range(0, len(x), 42)])
    rng = np.random.default_rng(seed)
    finals, dds = [], []
    for _ in range(n_samples):
        eq = np.concatenate([[1.0], np.cumprod(1 + rng.choice(weeks, size=len(weeks), replace=True))])
        finals.append(eq[-1] - 1)
        dds.append((eq / np.maximum.accumulate(eq) - 1).min())
    out["worst_case"] = {"weeks": int(len(weeks)), "pct_below_zero": round(float((np.array(finals) < 0).mean() * 100), 1),
                         "median_max_dd_pct": round(float(np.median(dds) * 100), 2),
                         "p5_max_dd_pct": round(float(np.percentile(dds, 5) * 100), 2)}

    # test 5 analogue: the basket's own positions, slid to a random other moment of the hidden year.
    # Sliding keeps how long, how big and how often it trades, and how the strategies move together;
    # it only breaks the timing against the market.
    r = close.pct_change().fillna(0)[h].to_numpy()
    p, c = P[h].to_numpy(), cost[h].to_numpy()
    real = float(np.log1p(p * r - c).sum())
    rng = np.random.default_rng(seed)
    shifts = rng.integers(1, len(r), size=n_samples)
    twins = np.array([np.log1p(np.roll(p, s) * r - np.roll(c, s)).sum() for s in shifts])
    out["luck_pct"] = round(float((real > twins).mean() * 100), 1)
    out["twin_median_return_pct"] = round(float((np.exp(np.median(twins)) - 1) * 100), 2)

    out["verdicts"] = {
        "test1": bool(hid["net_return_pct"] > 0 and hid["net_return_pct"] > hid["buy_hold_pct"]),
        "test2": bool(all(t["hid_return_pct"] > 0 for t in out["tweaks"])),
        "test3": bool(out["fees"]["2"] > 0),
        "test4": bool(out["worst_case"]["pct_below_zero"] < 25),
        "test5": bool(out["luck_pct"] >= 95),
    }
    return out, net
