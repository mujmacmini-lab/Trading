"""Usage:
    python backtest.py strategies/s001.py   evaluate one strategy and print every field
    python backtest.py --all                evaluate every strategies/s*.py, sort by status (OK first)
                                            then Sharpe (descending), print the table, save results.csv
                                            and print "<n> OK / <total> total"

Fixed rules of the engine (the same for every strategy):
  * Data: BTCUSDT perpetual, 4-hour candles (data/BTCUSDT_4h_insample.csv).
  * A strategy file defines PARAMS and signal(df, **params) returning 1 / 0 / -1 per bar.
  * The signal on a candle's close is held from the next candle.
  * Every position change costs COST_PER_SIDE (taker fee + slippage) per unit of turnover.
  * A signal that changes when later data is removed is rejected (look-ahead check).
  * A strategy needs at least MIN_TRADES trades to count.
"""
import glob
import importlib.util
import os
import sys

sys.dont_write_bytecode = True  # keep strategies/ free of __pycache__

import numpy as np
import pandas as pd

COST_PER_SIDE = 0.00055 + 0.00020  # taker fee + slippage
BARS_PER_YEAR = 6 * 365.25
MIN_TRADES = 30
N_CUTS = 8

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "BTCUSDT_4h_insample.csv")

FIELDS = [
    "file", "name", "family", "status", "reason",
    "net_return_pct", "cagr_pct", "sharpe", "max_drawdown_pct",
    "trades", "win_rate_pct", "profit_factor", "exposure_pct", "buy_hold_pct",
]


def load_data(path=DATA):
    df = pd.read_csv(path, parse_dates=["ts"], index_col="ts")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


def load_strategy(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "signal", None)):
        raise AttributeError("strategy has no signal(df, **params) function")
    return mod, dict(mod.PARAMS)


def clean_signal(sig, index):
    if isinstance(sig, pd.Series):
        s = sig.reindex(index)
    else:
        s = pd.Series(np.asarray(sig), index=index)
    s = s.astype(float)
    s = s.replace([np.inf, -np.inf], np.nan).fillna(0)
    return s.clip(-1, 1).round()


def lookahead_check(mod, params, df, full_sig):
    """Return None if clean, otherwise the failure message."""
    n = len(df)
    for c in np.linspace(int(n * 0.3), n - 1, N_CUTS).astype(int):
        part = df.iloc[:c].copy()
        sig = clean_signal(mod.signal(part, **params), part.index)
        diff = np.nonzero(sig.to_numpy() != full_sig.iloc[:c].to_numpy())[0]
        if len(diff):
            return (
                f"LOOK-AHEAD DETECTED: signal at {df.index[diff[0]]} changes "
                f"when data after {df.index[c - 1]} is removed"
            )
    return None


def simulate(df, sig, cost_mult=1.0):
    close = df["close"]
    pos = sig.shift(1).fillna(0)  # signal on a candle's close is held from the next candle
    r = close.pct_change().fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())
    net = pos * r - turn * COST_PER_SIDE * cost_mult

    c = COST_PER_SIDE * cost_mult
    p = pos.to_numpy()
    growth = (1 + pos * r).to_numpy()
    n = len(p)
    rows = []
    i = 0
    while i < n:
        if p[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and p[j + 1] == p[i]:
            j += 1
        still_open = j == n - 1
        ret = np.prod(growth[i:j + 1]) * (1 - c) ** (1 if still_open else 2) - 1
        rows.append({
            "entry": df.index[i],
            "exit": df.index[j],
            "side": int(p[i]),
            "bars": j - i + 1,
            "ret": ret,
        })
        i = j + 1
    trades = pd.DataFrame(rows, columns=["entry", "exit", "side", "bars", "ret"])
    return net, pos, trades


def metrics(net, pos, trades, close):
    equity = (1 + net).cumprod()
    final = float(equity.iloc[-1])
    years = len(net) / BARS_PER_YEAR
    cagr = final ** (1 / years) - 1 if final > 0 else -1.0
    std = net.std()
    sharpe = net.mean() / std * np.sqrt(BARS_PER_YEAR) if std > 0 else 0.0
    max_dd = (equity / equity.cummax() - 1).min()

    n_trades = len(trades)
    wins = trades.loc[trades["ret"] > 0, "ret"].sum()
    losses = trades.loc[trades["ret"] <= 0, "ret"].sum()
    win_rate = (trades["ret"] > 0).mean() if n_trades else 0.0
    if losses < 0:
        profit_factor = wins / -losses
    else:
        profit_factor = float("inf") if wins > 0 else 0.0

    out = {
        "net_return_pct": (final - 1) * 100,
        "cagr_pct": cagr * 100,
        "sharpe": sharpe,
        "max_drawdown_pct": max_dd * 100,
        "trades": n_trades,
        "win_rate_pct": win_rate * 100,
        "profit_factor": profit_factor,
        "exposure_pct": (pos != 0).mean() * 100,
        "buy_hold_pct": (close.iloc[-1] / close.iloc[0] - 1) * 100,
    }
    return {k: (v if k == "trades" else round(float(v), 2)) for k, v in out.items()}


def evaluate(path, df):
    res = {k: "" for k in FIELDS}
    res["file"] = os.path.basename(path)
    res["status"] = "ERROR"
    try:
        mod, params = load_strategy(path)
        res["name"] = getattr(mod, "NAME", "")
        res["family"] = getattr(mod, "FAMILY", "")
        full_sig = clean_signal(mod.signal(df.copy(), **params), df.index)
        problem = lookahead_check(mod, params, df, full_sig)
        if problem:
            res["status"] = "FAIL"
            res["reason"] = problem
            return res
        net, pos, trades = simulate(df, full_sig)
        res.update(metrics(net, pos, trades, df["close"]))
        if res["trades"] >= MIN_TRADES:
            res["status"] = "OK"
        else:
            res["status"] = "FAIL"
            res["reason"] = f"only {res['trades']} trades (minimum {MIN_TRADES})"
    except Exception as e:  # any exception gives ERROR
        res["status"] = "ERROR"
        res["reason"] = f"{type(e).__name__}: {e}"
    return res


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 1
    df = load_data(DATA)
    if argv[1] == "--all":
        paths = sorted(glob.glob(os.path.join(HERE, "strategies", "s*.py")))
        table = pd.DataFrame([evaluate(p, df) for p in paths], columns=FIELDS)
        rank = table["status"].map({"OK": 0}).fillna(1)
        sharpe = pd.to_numeric(table["sharpe"], errors="coerce")
        order = pd.DataFrame({"rank": rank, "sharpe": sharpe}).sort_values(
            ["rank", "sharpe"], ascending=[True, False], na_position="last", kind="stable"
        ).index
        table = table.loc[order].reset_index(drop=True)
        if len(table):
            print(table.to_string(index=False))
        table.to_csv(os.path.join(HERE, "results.csv"), index=False)
        print(f"{int((table['status'] == 'OK').sum())} OK / {len(table)} total")
    else:
        res = evaluate(argv[1], df)
        for k in FIELDS:
            print(f"{k:<17}: {res[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
