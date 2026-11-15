"""The exam: score both AIs' strategies on the hidden period.

Usage (from the project root):
    python exam/run_exam.py

Reads   fable/, opus/ (never written to) and hidden/BTCUSDT_4h_full.csv
Writes  exam/out/  (tables, charts, summary.json)  and  exam/RESULTS.md

If an AI's folder has no strategies/s*.py but a snapshot of its submission exists in
exam/out/submissions/<ai>/ (extracted byte-for-byte from that AI's git commit), the snapshot is scored.
"""
import glob
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)

import numpy as np
import pandas as pd

import audit
import charts
import engine as E
import report

AIS = {"fable": {"label": "Fable", "color": "#F59E0B"}, "opus": {"label": "Opus", "color": "#8B5CF6"}}


def submission_dir(ai):
    """(folder to score, where it came from) or (None, reason)."""
    live = os.path.join(ROOT, ai)
    if glob.glob(os.path.join(live, "strategies", "s*.py")):
        return live, f"{ai}/"
    snap = os.path.join(OUT, "submissions", ai)
    if glob.glob(os.path.join(snap, "strategies", "s*.py")):
        commit = open(snap + ".COMMIT").read().strip()[:7] if os.path.exists(snap + ".COMMIT") else "?"
        return snap, f"snapshot of git commit {commit} (exam/out/submissions/{ai}/), because {ai}/ here has no strategies"
    return None, f"{ai}/strategies/ is empty and no submission exists on any branch of the repository"


def main():
    os.makedirs(OUT, exist_ok=True)
    bt = E.load_engine(ROOT)
    full = bt.load_data(os.path.join(ROOT, "hidden", "BTCUSDT_4h_full.csv"))
    insample = bt.load_data(os.path.join(ROOT, "fable", "data", "BTCUSDT_4h_insample.csv"))
    hidden_mask = full.index >= E.CUT
    summary = {"hidden_bars": int(hidden_mask.sum()), "hidden_from": str(full.index[hidden_mask][0]),
               "hidden_to": str(full.index[-1]), "ais": {}}

    # ---- STEP 4 first: the engine must reproduce the reference numbers before anything is scored
    proof = E.proof_check(bt, full)
    summary["proof"] = [{"check": w, "expected": e, "got": g, "result": r} for w, e, g, r in proof]
    summary["proof_diagnostic"] = E.rule_b_near_miss(bt, full)
    print("STEP 4 proof check")
    for w, e, g, r in proof:
        print(f"  {w:<58} expected {e:>7}  got {g:>7}  {r}")

    # ---- STEP 1: cheat checks
    checks = audit.check_identical_engine(ROOT)
    log_flags = {}
    for ai in AIS:
        folder, source = submission_dir(ai)
        summary["ais"][ai] = {"label": AIS[ai]["label"], "source": source, "submitted": folder is not None}
        checks.append(audit.check_strategy_files(AIS[ai]["label"], folder or os.path.join(ROOT, ai)))
        if folder and folder != os.path.join(ROOT, ai):
            same = all(audit.same_bytes(os.path.join(folder, rel), os.path.join(ROOT, ai, rel))
                       for rel in ("backtest.py", os.path.join("data", "BTCUSDT_4h_insample.csv")))
            checks.append((f"{AIS[ai]['label']}: snapshot's backtest.py and in-sample CSV equal the ones in {ai}/",
                           "CLEAN" if same else "PROBLEM", "identical" if same else "DIFFERENT"))
        check, flags = audit.check_logs(AIS[ai]["label"], os.path.join(ROOT, ai))
        checks.append(check)
        log_flags[ai] = flags
    summary["cheat_checks"] = [{"check": c, "verdict": v, "detail": d} for c, v, d in checks]
    json.dump(log_flags, open(os.path.join(OUT, "log_flags.json"), "w"), indent=1)
    print("\nSTEP 1 cheat checks")
    for c, v, d in checks:
        print(f"  [{v:<7}] {c}  -- {d}")

    # ---- STEP 2 + 3: score each AI
    results = {}
    for ai, meta in AIS.items():
        folder, _ = submission_dir(ai)
        if folder is None:
            continue
        info = summary["ais"][ai]
        table, runs = E.score_ai(bt, folder, full, insample)
        champ = E.champion_id(os.path.join(folder, "FINAL.md")) if os.path.exists(os.path.join(folder, "FINAL.md")) else None
        info.update({"champion": champ, "strategies": int(len(table)), "scored": int(table["scored"].sum()),
                     "gate_fail": table.loc[~table["scored"], ["id", "gate", "gate_reason"]].to_dict("records")})
        luck = E.test5_luck(bt, runs, full)
        table["luck_pct"] = table["id"].map(luck)
        table.to_csv(os.path.join(OUT, f"scores_{ai}.csv"), index=False)
        results[ai] = {"table": table, "runs": runs, "champion": champ}
        if champ not in runs:
            info["champion_problem"] = f"champion {champ} was not scored"
            continue
        crow = table[table["id"] == champ].iloc[0]
        info["champion_name"] = crow["name"]
        info["champion_params"] = runs[champ]["params"]
        info["test1"] = E.test1_new_data(table, champ)
        tweaks, n_ok = E.test2_tweaks(bt, runs[champ]["path"], full)
        tweaks.to_csv(os.path.join(OUT, f"test2_tweaks_{ai}.csv"), index=False)
        info["test2"] = {"versions": tweaks.to_dict("records"), "profitable": n_ok, "total": int(len(tweaks))}
        info["test3"] = {str(k): v for k, v in E.test3_fees(bt, runs[champ]["path"], full).items()}
        info["test4"] = E.test4_worst_case(runs[champ]["hid_trades"]["ret"])
        scored = table[table["scored"]]
        info["test5"] = {"passed": int((scored["luck_pct"] >= 95).sum()), "of": int(len(scored)),
                         "champion_pct": float(crow["luck_pct"]), "median_pct": float(scored["luck_pct"].median())}
        info["should_have_picked"] = E.should_have_picked(table)
        t1, t2, t3, t4, t5 = info["test1"], info["test2"], info["test3"], info["test4"], info["test5"]
        info["verdicts"] = {   # pass rules, fixed before any strategy was scored
            "test1": bool(t1["champ_hid_return_pct"] > 0 and t1["champ_hid_return_pct"] > t1["buy_hold_pct"]),
            "test2": bool(t2["total"] > 0 and t2["profitable"] == t2["total"]),
            "test3": bool(t3["2"] > 0),
            "test4": bool(t4 is not None and t4["pct_below_zero"] < 25),
            "test5": bool(t5["champion_pct"] >= 95),
        }
        hid_top = scored.sort_values("hid_sharpe", ascending=False).head(10)
        info["hidden_top10"] = hid_top[["id", "name", "family", "is_rank", "is_sharpe", "hid_sharpe",
                                        "hid_net_return_pct", "hid_max_drawdown_pct", "hid_trades", "luck_pct"]].to_dict("records")
        info["by_family"] = (scored.groupby("family").agg(n=("id", "size"), profitable=("hid_net_return_pct", lambda x: int((x > 0).sum())),
                                                           median_hid_return=("hid_net_return_pct", "median"),
                                                           median_hid_sharpe=("hid_sharpe", "median")).round(2).reset_index().to_dict("records"))

    # ---- STEP 5: charts
    summary["charts"] = charts.make_all(results, full, AIS, OUT)

    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=str)
    report.write(summary, os.path.join(HERE, "RESULTS.md"))
    report.console(summary)


if __name__ == "__main__":
    main()
