"""Run every proof check of the build-off and print expected vs got.

Usage (after setup/download.py has written the data):
    python setup/proof_checks.py

  a) the template, copied to fable/strategies/s001.py, reproduces the original engine's numbers
  b) a cheating strategy that uses close.shift(-1) is rejected with LOOK-AHEAD DETECTED
  c) two calibration rules (setup/calibration/) reproduce the original engine's numbers
  d) both test strategies are deleted again and fable/ and opus/ are byte-identical
Also lists each data file with its date range and candle count, and checks that no file
outside hidden/ contains a candle from November 2025 or later.
"""
import filecmp
import importlib.util
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FABLE = os.path.join(ROOT, "fable")
OPUS = os.path.join(ROOT, "opus")
EXAM_START = pd.Timestamp("2025-11-01 00:00", tz="UTC")

CHEAT = '''"""Cheating strategy: looks at the next candle's close."""
import numpy as np

NAME = "Cheat"
FAMILY = "cheat"
IDEA = "Long if the NEXT close is higher, short if it is lower."
PARAMS = {}


def signal(df):
    close = df["close"]
    return np.sign(close.shift(-1) - close)
'''

rows = []


def record(check, expected, got):
    rows.append((check, str(expected), str(got), "MATCH" if str(expected) == str(got) else "NO MATCH"))


def run_cli(path):
    """Run `python backtest.py <path>` inside fable/ and parse the printed fields."""
    out = subprocess.run([sys.executable, "backtest.py", path], cwd=FABLE,
                         capture_output=True, text=True).stdout
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in out.splitlines() if ":" in line)}


def tree(folder):
    files = {}
    for base, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for d in dirs:
            files[os.path.relpath(os.path.join(base, d), folder) + os.sep] = None
        for name in names:
            full = os.path.join(base, name)
            files[os.path.relpath(full, folder)] = full
    return files


def identical(a, b):
    ta, tb = tree(a), tree(b)
    if set(ta) != set(tb):
        return False
    return all(ta[k] is None or filecmp.cmp(ta[k], tb[k], shallow=False) for k in ta)


def main():
    for folder in (FABLE, OPUS):
        os.makedirs(os.path.join(folder, "strategies"), exist_ok=True)  # git does not keep empty folders

    # ---- data files -------------------------------------------------------------
    print("DATA FILES")
    leaks = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in sorted(names):
            if not name.endswith(".csv"):
                continue
            full = os.path.join(base, name)
            head = pd.read_csv(full, nrows=0)
            if "ts" not in head.columns:
                continue
            ts = pd.to_datetime(pd.read_csv(full, usecols=["ts"])["ts"], utc=True)
            rel = os.path.relpath(full, ROOT)
            print(f"  {rel:<40} {ts.iloc[0]} -> {ts.iloc[-1]}   {len(ts):>6} candles")
            if not rel.startswith("hidden" + os.sep) and (ts >= EXAM_START).any():
                leaks.append(rel)
    record("exam candles outside hidden/", "none", ", ".join(leaks) if leaks else "none")

    # ---- a) template ------------------------------------------------------------
    s001 = os.path.join(FABLE, "strategies", "s001.py")
    shutil.copyfile(os.path.join(FABLE, "strategy_template.py"), s001)
    res = run_cli("strategies/s001.py")
    record("a) template: net return %", "75.95", res.get("net_return_pct"))
    record("a) template: Sharpe", "0.47", res.get("sharpe"))
    record("a) template: trades", "143", res.get("trades"))
    record("a) template: buy & hold %", "1622.3", res.get("buy_hold_pct"))

    # ---- b) cheat ---------------------------------------------------------------
    s002 = os.path.join(FABLE, "strategies", "s002.py")
    with open(s002, "w") as f:
        f.write(CHEAT)
    res = run_cli("strategies/s002.py")
    cheat_msg = res.get("reason", "")
    rejected = res.get("status") == "FAIL" and cheat_msg.startswith("LOOK-AHEAD DETECTED")
    record("b) cheat is rejected", "LOOK-AHEAD DETECTED", "LOOK-AHEAD DETECTED" if rejected else res.get("status"))

    # ---- c) calibration, same backtester, in-sample data --------------------------
    spec = importlib.util.spec_from_file_location("backtest", os.path.join(FABLE, "backtest.py"))
    bt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bt)
    df = bt.load_data(bt.DATA)
    for label, fname, exp in [("c) rule A", "rule_a.py", ("3176.75", "1.66", "184")),
                              ("c) rule B", "rule_b.py", ("1150.24", "1.06", "137"))]:
        r = bt.evaluate(os.path.join(ROOT, "setup", "calibration", fname), df)
        record(f"{label}: net return %", exp[0], r["net_return_pct"])
        record(f"{label}: Sharpe", exp[1], r["sharpe"])
        record(f"{label}: trades", exp[2], r["trades"])

    # ---- d) clean up --------------------------------------------------------------
    os.remove(s001)
    os.remove(s002)
    for folder in (FABLE, OPUS):
        shutil.rmtree(os.path.join(folder, "strategies", "__pycache__"), ignore_errors=True)
    left = os.listdir(os.path.join(FABLE, "strategies"))
    record("d) fable/strategies/ is empty", "empty", "empty" if not left else ", ".join(left))
    record("d) fable/ and opus/ byte-identical", "identical", "identical" if identical(FABLE, OPUS) else "DIFFERENT")

    # ---- report -------------------------------------------------------------------
    print("\nPROOF CHECKS")
    w = max(len(r[0]) for r in rows)
    print(f"  {'check':<{w}}  {'expected':>20}  {'got':>20}  result")
    for check, expected, got, verdict in rows:
        print(f"  {check:<{w}}  {expected:>20}  {got:>20}  {verdict}")
    print(f"\nCHEAT REJECTION MESSAGE\n  {cheat_msg}")
    bad = [r for r in rows if r[3] != "MATCH"]
    print(f"\n{len(rows) - len(bad)} / {len(rows)} checks match")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
