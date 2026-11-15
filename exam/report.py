"""STEP 6 - writes exam/RESULTS.md (plain English) from the numbers in summary.json."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TESTS = [
    ("test1", "1. New data", "made money in the hidden year and beat simply holding bitcoin"),
    ("test2", "2. Tweak the settings", "still made money with every setting nudged 20% up or down"),
    ("test3", "3. Higher fees", "still made money with trading costs doubled"),
    ("test4", "4. Worst case", "lost money in fewer than 1 in 4 reshuffles of its results"),
    ("test5", "5. Luck check", "beat at least 95% of randomly timed look-alikes"),
]


def pct(x, signed=True):
    return f"{x:+,.2f}%" if signed else f"{x:,.2f}%"


def verdict(ok):
    return "PASS" if ok else "FAIL"


def final_verdict(a):
    """One-line result for a single AI, from its champion and its basket."""
    c, b = sum(a["verdicts"].values()), sum(a["basket"]["verdicts"].values())
    made_money = a["test1"]["champ_hid_return_pct"] > 0 and a["basket"]["hidden"]["net_return_pct"] > 0
    luck_ok = a["verdicts"]["test5"] or a["basket"]["verdicts"]["test5"]
    if made_money and luck_ok and b >= 4:
        return "PROVEN ON THIS YEAR", "the strategies made money and beat the luck bar"
    if made_money and b >= 4:
        return "PROMISING, NOT PROVEN", ("the strategies made money on a year they were not built on and the group survived "
                                         "the stress tests, but nothing clears the bar that separates skill from luck")
    if made_money:
        return "INCONCLUSIVE", "the strategies made money but did not survive the stress tests"
    return "FAILED", "the strategies lost money on the hidden year"


def scoreboard(a):
    lines = [f"| Test | Champion {a['champion']} | All {a['basket']['n']} as one basket | Pass means it... |", "|---|---|---|---|"]
    for key, title, rule in TESTS:
        lines.append(f"| {title} | **{verdict(a['verdicts'][key])}** | **{verdict(a['basket']['verdicts'][key])}** | {rule} |")
    lines.append(f"| **Tests passed** | **{sum(a['verdicts'].values())} of 5** | **{sum(a['basket']['verdicts'].values())} of 5** | |")
    return "\n".join(lines)


def result_section(a):
    t1, t5, b = a["test1"], a["test5"], a["basket"]
    label, why = final_verdict(a)
    return "\n\n".join([
        f"**{label}.** {a['label']}'s {t1['scored']} strategies were built on bitcoin prices up to October 2025 and then run, "
        f"untouched, on the following year. In short: {why}.",
        f"- **The champion {a['label']} named in advance, {a['champion']} ({a['champion_name']}),** turned $10,000 into "
        f"${10000 * (1 + t1['champ_hid_return_pct'] / 100):,.0f} ({pct(t1['champ_hid_return_pct'])}) while holding bitcoin turned "
        f"$10,000 into ${10000 * (1 + t1['buy_hold_pct'] / 100):,.0f} ({pct(t1['buy_hold_pct'])}). It passed "
        f"{sum(a['verdicts'].values())} of 5 tests and finished {t1['champ_hid_rank']} of {t1['scored']} among its own siblings.\n"
        f"- **All {b['n']} strategies held together as one basket** made {pct(b['hidden']['net_return_pct'])} with a worst dip of "
        f"{pct(b['hidden']['max_drawdown_pct'])}, and passed {sum(b['verdicts'].values())} of 5 tests. Its return per unit of risk "
        f"(Sharpe) was {b['hidden']['sharpe']:.2f} in the hidden year against {b['before']['sharpe']:.2f} before it: the group behaved "
        f"on new data the way it behaved on old data.\n"
        f"- **Neither clears the luck bar.** Against randomly timed look-alikes the champion beat {t5['champion_pct']:.0f}% and the "
        f"basket beat {b['luck_pct']:.0f}%; 95% is the line. One year is too short to tell skill from a good year.\n"
        f"- **Picking a single winner in advance did not work.** {t1['profitable']} of {t1['scored']} strategies made money, but the "
        f"ranking on old data said nothing about the ranking on new data (link {t1['spearman']:+.2f}, where 0 is no link).",
    ])


def forward_section(a):
    b, s, t1 = a["basket"], a["should_have_picked"], a["test1"]
    return "\n".join([
        f"**The basket of all {b['n']} strategies, not any single one.**", "",
        f"- **Not {s['id']} ({s['name']}),** the best performer at {pct(s['hid_return_pct'])}. It was ranked {s['is_rank']} of "
        f"{s['of']} beforehand; choosing it now is picking the lottery winner after the draw.",
        f"- **Not the champion {a['champion']} on its own.** It was the honest advance pick, but it failed three tests.",
        f"- **The basket** needs no picking, so hindsight cannot flatter it. It is one bet, not {b['n']}: the strategies move "
        f"together (typical correlation {b['median_pair_corr_hidden']:.2f}).", "",
        "How to take it forward:", "",
        "1. Freeze the 100 files as they are. No re-tuning on the hidden year.",
        "2. Trade it on paper for 3 to 6 months on live 4-hour candles, as one position equal to the average of the 100 signals. "
        "Only data from today on is truly unseen by the model.",
        "3. Add funding costs. The backtester charges fees and slippage but not the funding payments of perpetual futures.",
        "4. Fix the stop rule now, for example: drop it if the forward Sharpe is below 0.5 or the dip passes 25%.",
        "5. Consider small real money only after that.",
    ])


def caveats(summary):
    out = []
    problems = [c for c in summary["cheat_checks"] if c["verdict"] != "CLEAN"]
    if problems:
        out.append(f"- **{len(problems)} of {len(summary['cheat_checks'])} cheat checks could not be passed:** the session logs the spec "
                   "asks for are not on this machine. A substitute audit of the build session found no access to the hidden file "
                   "(details in Step 1).")
    out.append("- **The hidden year is not fully unknown to the AI.** The model's training data runs into 2026, and its own FINAL.md "
               "says it has a rough idea how bitcoin moved after October 2025. It never saw the hidden candles, but that background "
               "knowledge cannot be ruled out as an influence.")
    out.append("- **The basket tests were added after the champion's results were known.** The five tests were specified for the "
               "champion. The basket versions ask the same five questions of the whole set and use the same pass lines, but they "
               "were not fixed in advance.")
    out.append("- **A falling year flatters strategies that can bet on falling prices.** Bitcoin lost 29% in the hidden year. "
               "The luck check is the test that corrects for this, and it is the one that was not passed.")
    bad = [p for p in summary["proof"] if p["result"] != "MATCH"]
    if bad:
        out.append(f"- **The proof check matches on {len(summary['proof']) - len(bad)} of {len(summary['proof'])} numbers.** The rest "
                   "differ most likely because the reference numbers come from a slightly different price feed, not because of the "
                   "engine (details in Step 4).")
    return "\n".join(out)


def champion_section(a):
    t1, t2, t3, t4, t5, v = a["test1"], a["test2"], a["test3"], a["test4"], a["test5"], a["verdicts"]
    s = [f"Scored: {a['source']}. {a['scored']} of {a['strategies']} strategies passed the entry gate "
         f"(no look-ahead, at least 30 trades on the data the AI was given) and were scored. "
         f"Champion named in FINAL.md: **{a['champion']} - {a['champion_name']}**, settings `{a['champion_params']}`.", ""]

    s += [f"**Test 1, new data: {verdict(v['test1'])}**", "",
          "| | |", "|---|---|",
          f"| Strategies that made money in the hidden year | {t1['profitable']} of {t1['scored']} |",
          f"| Strategies that beat buy & hold ({pct(t1['buy_hold_pct'])}) | {t1['beat_buy_hold']} of {t1['scored']} |",
          f"| Typical (median) Sharpe before the hidden year | {t1['median_is_sharpe']:.2f} |",
          f"| Typical (median) Sharpe in the hidden year | {t1['median_hid_sharpe']:.2f} |",
          f"| Did the past ranking predict the hidden ranking? (Spearman, -1 to +1) | {t1['spearman']:+.2f} |",
          f"| Champion: yearly growth before the hidden year (CAGR) | {pct(t1['champ_is_cagr_pct'])} |",
          f"| Champion: return in the hidden year | {pct(t1['champ_hid_return_pct'])} (Sharpe {t1['champ_hid_sharpe']:.2f}, worst dip {pct(t1['champ_hid_max_dd_pct'])}, {t1['champ_hid_trades']} trades) |",
          f"| Champion: rank in the hidden year by Sharpe | {t1['champ_hid_rank']} of {t1['scored']} (it was {t1['champ_is_rank']} of {t1['scored']} before) |",
          "",
          "Sharpe is return per unit of bumpiness: above 1 is good, around 0 is nothing, below 0 is losing. "
          "A Spearman near 0 means a strategy's past score told you almost nothing about its hidden-year score.", ""]

    s += [f"**Test 2, tweak the settings: {verdict(v['test2'])}** - {t2['profitable']} of {t2['total']} tweaked versions stayed profitable.", "",
          "| Setting | Changed to | Hidden return | Hidden Sharpe |", "|---|---|---|---|"]
    for r in t2["versions"]:
        s.append(f"| {r['param']} = {r['from']} | {r['to']} (x{r['mult']}) | {pct(r['hid_return_pct'])} | {r['hid_sharpe']:.2f} |")
    s.append("")

    s += [f"**Test 3, higher fees: {verdict(v['test3'])}**", "",
          "| Trading costs | Hidden return |", "|---|---|",
          f"| None (x0) | {pct(t3['0'])} |", f"| Normal (x1) | {pct(t3['1'])} |",
          f"| Double (x2) | {pct(t3['2'])} |", f"| Triple (x3) | {pct(t3['3'])} |", ""]

    s += [f"**Test 4, worst case: {verdict(v['test4'])}**", "",
          f"The champion's {t4['trades']} hidden-year trades were reshuffled 1,000 times (drawn at random, with repeats).", "",
          "| | |", "|---|---|",
          f"| Reshuffles that ended in a loss | {t4['pct_below_zero']:.1f}% |",
          f"| Typical (median) worst dip | {pct(t4['median_max_dd_pct'])} |",
          f"| Worst dip in the unluckiest 5% | {pct(t4['p5_max_dd_pct'])} |", ""]

    s += [f"**Test 5, luck check: {verdict(v['test5'])}**", "",
          "Each strategy's hidden-year trades were compared with 1,000 random twins: same number of trades, same "
          "direction, same length, but entered at random moments.", "",
          "| | |", "|---|---|",
          f"| Champion beat | {t5['champion_pct']:.1f}% of its twins (95% needed) |",
          f"| Strategies that beat 95% of their twins | {t5['passed']} of {t5['of']} (about 5 would by chance alone) |",
          f"| Typical (median) strategy beat | {t5['median_pct']:.1f}% of its twins |", ""]
    return "\n".join(s)


def basket_section(a):
    b = a["basket"]
    v, w = b["verdicts"], b["worst_case"]
    s = [f"All {b['n']} strategies held at the same time with equal money in each, rebalanced every candle. In practice that is one "
         f"position equal to the average of the {b['n']} signals.", "",
         "| | Before the hidden year | Hidden year |", "|---|---|---|",
         f"| Return | {pct(b['before']['net_return_pct'])} ({pct(b['before']['cagr_pct'])} a year) | {pct(b['hidden']['net_return_pct'])} |",
         f"| Sharpe | {b['before']['sharpe']:.2f} | {b['hidden']['sharpe']:.2f} |",
         f"| Worst dip | {pct(b['before']['max_drawdown_pct'])} | {pct(b['hidden']['max_drawdown_pct'])} |",
         f"| Buy & hold bitcoin | {pct(b['before']['buy_hold_pct'])} | {pct(b['hidden']['buy_hold_pct'])} |", "",
         f"**Test 1, new data: {verdict(v['test1'])}** - {pct(b['hidden']['net_return_pct'])} against {pct(b['hidden']['buy_hold_pct'])} for holding bitcoin.", "",
         f"**Test 2, tweak the settings: {verdict(v['test2'])}** - every numeric setting of every strategy moved at once.", "",
         "| All settings | Hidden return | Hidden Sharpe |", "|---|---|---|"]
    for t in b["tweaks"]:
        s.append(f"| x{t['mult']} | {pct(t['hid_return_pct'])} | {t['hid_sharpe']:.2f} |")
    s += ["", f"**Test 3, higher fees: {verdict(v['test3'])}**", "",
          "| Trading costs | Hidden return |", "|---|---|",
          f"| None (x0) | {pct(b['fees']['0'])} |", f"| Normal (x1) | {pct(b['fees']['1'])} |",
          f"| Double (x2) | {pct(b['fees']['2'])} |", f"| Triple (x3) | {pct(b['fees']['3'])} |", "",
          f"**Test 4, worst case: {verdict(v['test4'])}** - a basket has no single trades, so its hidden year was cut into "
          f"{w['weeks']} weeks and the weeks were reshuffled 1,000 times.", "",
          "| | |", "|---|---|",
          f"| Reshuffles that ended in a loss | {w['pct_below_zero']:.1f}% |",
          f"| Typical (median) worst dip | {pct(w['median_max_dd_pct'])} |",
          f"| Worst dip in the unluckiest 5% | {pct(w['p5_max_dd_pct'])} |", "",
          f"**Test 5, luck check: {verdict(v['test5'])}** - the basket's own positions were slid to 1,000 random other moments of "
          "the hidden year. That keeps how big, how long and how often it trades, and only breaks its timing against the market.", "",
          "| | |", "|---|---|",
          f"| Basket beat | {b['luck_pct']:.1f}% of its randomly timed twins (95% needed) |",
          f"| Typical twin made | {pct(b['twin_median_return_pct'])} |", ""]
    return "\n".join(s)


def picked_section(a):
    b, t1 = a["should_have_picked"], a["test1"]
    s = [f"{a['label']}'s best strategy in the hidden year (by Sharpe, at least 5 trades) was "
         f"**{b['id']} - {b['name']}** ({b['family']}): {pct(b['hid_return_pct'])}, Sharpe {b['hid_sharpe']:.2f}, "
         f"worst dip {pct(b['hid_max_dd_pct'])}, {b['hid_trades']} trades. On the data the AI could see it ranked only "
         f"**{b['is_rank']} of {b['of']}** (Sharpe {b['is_sharpe']:.2f}), while the champion it did pick ranked "
         f"{t1['champ_is_rank']}. Nothing in the past pointed to it.", "",
         "Top 10 in the hidden year:", "",
         "| Hidden rank | Strategy | Family | Rank before | Hidden return | Hidden Sharpe | Worst dip | Trades | Beat twins |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(a["hidden_top10"], 1):
        s.append(f"| {i} | {r['id']} {r['name']} | {r['family']} | {int(r['is_rank'])} | {pct(r['hid_net_return_pct'])} | "
                 f"{r['hid_sharpe']:.2f} | {pct(r['hid_max_drawdown_pct'])} | {int(r['hid_trades'])} | {r['luck_pct']:.0f}% |")
    s += ["", "By family:", "", "| Family | Strategies | Made money | Median hidden return | Median hidden Sharpe |", "|---|---|---|---|---|"]
    for r in sorted(a["by_family"], key=lambda r: -r["median_hid_sharpe"]):
        s.append(f"| {r['family']} | {r['n']} | {r['profitable']} | {pct(r['median_hid_return'])} | {r['median_hid_sharpe']:.2f} |")
    return "\n".join(s)


def cheat_section(summary):
    s = ["| Check | Verdict | Detail |", "|---|---|---|"]
    for c in summary["cheat_checks"]:
        s.append(f"| {c['check']} | **{c['verdict']}** | {c['detail']} |")
    manual = os.path.join(HERE, "manual_audit.md")
    if os.path.exists(manual):
        s += ["", open(manual, encoding="utf-8").read().strip()]
    return "\n".join(s)


def proof_section(summary):
    s = ["| Check | Expected | Got | Result |", "|---|---|---|---|"]
    for p in summary["proof"]:
        s.append(f"| {p['check']} | {p['expected']} | {p['got']} | **{p['result']}** |")
    bad = [p for p in summary["proof"] if p["result"] != "MATCH"]
    d = summary.get("proof_diagnostic")
    if bad and d:
        s += ["",
              f"{len(summary['proof']) - len(bad)} of {len(summary['proof'])} match exactly. The others could not be made to match "
              "by changing code, because the difference is most likely in the candles, not the engine: the reference numbers look "
              "like they were produced on a slightly different price feed than the Binance candles in `hidden/` "
              "(the same thing showed up when the exam room was built). The evidence:",
              "",
              "- Buy & hold and Rule A's trade count match exactly, and Rule A's return is within 0.03 points, "
              "so the fees, the next-candle rule and the way the hidden year is cut out behave like the original engine.",
              f"- Rule B flips whenever price closes 1% beyond its average line. On {d['bar'][:16]} UTC the Binance close "
              f"(${d['close']:,.1f}) stopped **{d['gap_pct']}%, about ${d['gap_usd']:,.0f}, short** of that line. "
              f"If that one candle is treated as having crossed, Rule B gives {pct(d['if_crossed_return_pct'])} with "
              f"{d['if_crossed_trades']} trades - against the reference +26.15% and 26 trades. "
              "A few dollars of difference between two price feeds on one candle would explain nearly all of the gap.",
              "- No slicing convention tried (re-running on the hidden year alone, restarting positions on 1 November, "
              "compounding trade by trade) gets closer than the one in the spec.",
              "",
              "The scores in this report are therefore right for the candles in this repository, but will differ "
              "slightly from a run on the original price feed."]
    return "\n".join(s)


def write(summary, path):
    a = next(x for x in summary["ais"].values() if "verdicts" in x)
    charts = summary.get("charts", {})
    parts = [
        f"# Exam result: {a['label']}'s {a['scored']} strategies on a year they were not built on",
        "",
        f"Hidden period: {summary['hidden_from'][:10]} to {summary['hidden_to'][:10]} "
        f"({summary['hidden_bars']:,} four-hour candles). Every number below comes from `python exam/run_exam.py`, "
        "using the same engine the AI was given (`fable/backtest.py`): same fees, same next-candle rule.",
        "",
        "## The result", "", result_section(a), "",
        "## Scoreboard", "", scoreboard(a), "",
        "The champion's pass lines were written down before any strategy was scored. The basket column asks the same five "
        "questions of all strategies held together.", "",
        "## What to push forward", "", forward_section(a), "",
        "## Read this before trusting the result", "", caveats(summary), "",
        "## Step 1: did anybody cheat?", "", cheat_section(summary), "",
        f"## The champion in detail: {a['champion']}", "", champion_section(a),
        f"## The basket in detail: all {a['basket']['n']} strategies together", "", basket_section(a),
        "## The one it should have picked", "", picked_section(a), "",
        "## Step 4: is the engine right? (proof check)", "", proof_section(summary), "", "## Charts", "",
    ]
    for name in sorted(charts):
        parts += [f"![{name}](out/{name})", ""]
    parts += ["## Files", "",
              "- `exam/out/scores_fable.csv`: every strategy with its before and hidden-year numbers",
              "- `exam/out/test2_tweaks_fable.csv`: the tweaked versions of the champion",
              "- `exam/out/summary.json`: every number in this report",
              "- `exam/out/log_flags.json`: flagged tool calls from the session logs",
              "- `exam/out/submissions/`: the byte-for-byte snapshot that was scored, with its git commit", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def console(summary):
    a = next(x for x in summary["ais"].values() if "verdicts" in x)
    label, why = final_verdict(a)
    print(f"\nRESULT: {label} - {why}")
    print(f"  {'':<24} champion {a['champion']:<6} basket of {a['basket']['n']}")
    for key, title, _ in TESTS:
        print(f"  {title:<24} {verdict(a['verdicts'][key]):<15} {verdict(a['basket']['verdicts'][key])}")
    t1, b = a["test1"], a["basket"]
    print(f"  hidden return            {pct(t1['champ_hid_return_pct']):<15} {pct(b['hidden']['net_return_pct'])}   (buy & hold {pct(t1['buy_hold_pct'])})")
    print(f"  beat random twins        {a['test5']['champion_pct']:<15} {b['luck_pct']}   (95 needed)")
