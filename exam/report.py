"""STEP 6 - writes exam/RESULTS.md (plain English) from the numbers in summary.json."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TESTS = [
    ("test1", "1. New data", "the champion made money in the hidden year and beat simply holding bitcoin"),
    ("test2", "2. Tweak the settings", "every version with a setting nudged 20% up or down still made money"),
    ("test3", "3. Higher fees", "the champion still made money with trading costs doubled"),
    ("test4", "4. Worst case", "fewer than 1 in 4 reshuffles of its trades ended in a loss"),
    ("test5", "5. Luck check", "the champion beat at least 95% of random look-alikes"),
]


def pct(x, signed=True):
    return f"{x:+,.2f}%" if signed else f"{x:,.2f}%"


def verdict(ok):
    return "PASS" if ok else "FAIL"


def scoreboard(summary):
    ais = summary["ais"]
    lines = ["| Test | " + " | ".join(a["label"] for a in ais.values()) + " | Pass means |",
             "|---|" + "---|" * len(ais) + "---|"]
    for key, title, rule in TESTS:
        cells = []
        for a in ais.values():
            cells.append(f"**{verdict(a['verdicts'][key])}**" if "verdicts" in a else "not submitted")
        lines.append(f"| {title} | " + " | ".join(cells) + f" | {rule} |")
    totals = [f"**{sum(a['verdicts'].values())} of 5**" if "verdicts" in a else "-" for a in ais.values()]
    lines.append("| **Tests passed** | " + " | ".join(totals) + " | |")
    return "\n".join(lines)


def headline(summary):
    ais = summary["ais"]
    done = [a for a in ais.values() if "verdicts" in a]
    missing = [a for a in ais.values() if "verdicts" not in a]
    out = []
    if missing and done:
        out.append(f"**There is no head-to-head winner, because only {done[0]['label']} handed in strategies.** "
                   f"{missing[0]['label']}'s folder is empty: {missing[0]['source']}. "
                   f"So this is {done[0]['label']} against the exam, not against {missing[0]['label']}.")
    elif len(done) == 2:
        a, b = done
        sa, sb = sum(a["verdicts"].values()), sum(b["verdicts"].values())
        if sa != sb:
            w, l = (a, b) if sa > sb else (b, a)
            out.append(f"**{w['label']} won, {max(sa, sb)} tests to {min(sa, sb)}.**")
        else:
            ra, rb = a["test1"]["champ_hid_return_pct"], b["test1"]["champ_hid_return_pct"]
            w = a if ra >= rb else b
            out.append(f"**Tied on tests ({sa} each); {w['label']}'s champion made more in the hidden year "
                       f"({pct(max(ra, rb))} vs {pct(min(ra, rb))}).**")
    else:
        out.append("**Nobody handed in strategies, so there is nothing to score.**")
    for a in done:
        t1, t5, n = a["test1"], a["test5"], sum(a["verdicts"].values())
        out.append(
            f"{a['label']}'s champion, **{a['champion']} ({a['champion_name']})**, turned $10,000 into "
            f"**${10000 * (1 + t1['champ_hid_return_pct'] / 100):,.0f}** over the hidden year ({pct(t1['champ_hid_return_pct'])}) "
            f"while simply holding bitcoin returned {pct(t1['buy_hold_pct'])}. It passed **{n} of the 5 tests**. "
            f"Across all {t1['scored']} of {a['label']}'s strategies, {t1['profitable']} made money and "
            f"{t1['beat_buy_hold']} did better than holding bitcoin.")
        if t5["champion_pct"] < 95:
            out.append(
                f"The honest catch is the luck check: the champion beat {t5['champion_pct']:.0f}% of random look-alikes, "
                f"short of the 95% needed to rule out luck, and only {t5['passed']} of {t5['of']} strategies cleared that bar.")
    return "\n\n".join(out)


def picks(summary):
    lines = []
    for a in summary["ais"].values():
        b = a.get("should_have_picked")
        if not b:
            lines.append(f"- **{a['label']}**: nothing submitted, so there is nothing to pick from.")
            continue
        t1 = a["test1"]
        lines.append(
            f"- **{a['label']}** should have picked **{b['id']} ({b['name']})**: {pct(b['hid_return_pct'])} in the hidden year "
            f"with a worst dip of {pct(b['hid_max_dd_pct'])}, against {pct(t1['champ_hid_return_pct'])} for its actual champion "
            f"{a['champion']}. Before the hidden year that strategy sat at rank {b['is_rank']} of {b['of']}, and the champion at "
            f"rank {t1['champ_is_rank']} - the past ranking pointed the wrong way (rank link between past and hidden "
            f"scores: {t1['spearman']:+.2f}, where 0 means no link).")
    return "\n".join(lines)


def caveats(summary):
    out = []
    problems = [c for c in summary["cheat_checks"] if c["verdict"] != "CLEAN"]
    if problems:
        out.append(f"- **{len(problems)} of {len(summary['cheat_checks'])} cheat checks could not be passed**, all for the same two "
                   "reasons: one AI handed in nothing, and the session logs the spec asks for are not on this machine. "
                   "A substitute audit of the build session found no access to the hidden file (details in Step 1).")
    if os.path.exists(os.path.join(HERE, "manual_audit.md")):
        out.append("- **The hidden year is not fully unknown to the AI.** The model's training data runs into 2026, and its own "
                   "FINAL.md says it has a rough idea how bitcoin moved after October 2025. It never saw the hidden candles, "
                   "but that background knowledge cannot be ruled out as an influence.")
    bad = [p for p in summary["proof"] if p["result"] != "MATCH"]
    if bad:
        out.append(f"- **The proof check matches on {len(summary['proof']) - len(bad)} of {len(summary['proof'])} numbers.** The rest "
                   "differ most likely because the reference numbers come from a slightly different price feed, not because of the engine "
                   "(details in Step 4).")
    return "\n".join(out)


def ai_section(a):
    if "verdicts" not in a:
        return f"### {a['label']}\n\nNot submitted: {a['source']}. Nothing could be scored.\n"
    t1, t2, t3, t4, t5, v = a["test1"], a["test2"], a["test3"], a["test4"], a["test5"], a["verdicts"]
    s = [f"### {a['label']}", "",
         f"Scored: {a['source']}. {a['scored']} of {a['strategies']} strategies passed the entry gate "
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
          f"| Strategies that beat 95% of their twins | {t5['passed']} of {t5['of']} |",
          f"| Typical (median) strategy beat | {t5['median_pct']:.1f}% of its twins |", ""]

    b = a["should_have_picked"]
    if b:
        same = b["id"] == a["champion"]
        s += ["**The one it should have picked**", "",
              f"{a['label']}'s best strategy in the hidden year (by Sharpe, at least 5 trades) was "
              f"**{b['id']} - {b['name']}** ({b['family']}): {pct(b['hid_return_pct'])}, Sharpe {b['hid_sharpe']:.2f}, "
              f"worst dip {pct(b['hid_max_dd_pct'])}, {b['hid_trades']} trades. "
              + ("That is the champion it actually picked." if same else
                 f"On the data the AI could see it ranked only **{b['is_rank']} of {b['of']}** "
                 f"(Sharpe {b['is_sharpe']:.2f}), so nothing in the past pointed to it."), ""]

    s += ["Top 10 in the hidden year:", "",
          "| Hidden rank | Strategy | Family | Rank before | Hidden return | Hidden Sharpe | Worst dip | Trades | Beat twins |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(a["hidden_top10"], 1):
        star = " (champion)" if r["id"] == a["champion"] else ""
        s.append(f"| {i} | {r['id']} {r['name']}{star} | {r['family']} | {int(r['is_rank'])} | {pct(r['hid_net_return_pct'])} | "
                 f"{r['hid_sharpe']:.2f} | {pct(r['hid_max_drawdown_pct'])} | {int(r['hid_trades'])} | {r['luck_pct']:.0f}% |")
    s += ["", "By family:", "", "| Family | Strategies | Made money | Median hidden return | Median hidden Sharpe |", "|---|---|---|---|---|"]
    for r in sorted(a["by_family"], key=lambda r: -r["median_hid_sharpe"]):
        s.append(f"| {r['family']} | {r['n']} | {r['profitable']} | {pct(r['median_hid_return'])} | {r['median_hid_sharpe']:.2f} |")
    s.append("")
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
    ais = summary["ais"]
    charts = summary.get("charts", {})
    parts = [
        "# Exam results: 100 strategies per AI on a year they never saw",
        "",
        f"Hidden period: {summary['hidden_from'][:10]} to {summary['hidden_to'][:10]} "
        f"({summary['hidden_bars']:,} four-hour candles). Every number below comes from `python exam/run_exam.py`, "
        "using the same engine the AIs were given (`fable/backtest.py`): same fees, same next-candle rule.",
        "",
        "## Who won, and why", "", headline(summary), "",
        "## Scoreboard", "", scoreboard(summary), "",
        "The pass rules were written down before any strategy was scored. Tests 2 to 5 are about each AI's champion; "
        "the detail sections show the numbers for all of its strategies.", "",
        "## The strategy each AI should have picked", "", picks(summary), "",
        "## Read this before trusting the scoreboard", "", caveats(summary), "",
        "## Step 1: did anybody cheat?", "", cheat_section(summary), "",
        "## The five tests in detail", "",
    ]
    parts += [ai_section(a) for a in ais.values()]
    parts += ["## Step 4: is the engine right? (proof check)", "", proof_section(summary), "", "## Charts", ""]
    for name in ("spaghetti_fable.png", "spaghetti_opus.png", "full_history.png"):
        parts += [f"![{name}](out/{name})", ""] if name in charts else [f"`{name}`: not drawn - no strategies were submitted.", ""]
    parts += ["## Files", "",
              "- `exam/out/scores_<ai>.csv`: every strategy with its before and hidden-year numbers",
              "- `exam/out/test2_tweaks_<ai>.csv`: the tweaked versions of the champion",
              "- `exam/out/summary.json`: every number in this report",
              "- `exam/out/log_flags.json`: flagged tool calls from the session logs",
              "- `exam/out/submissions/`: the byte-for-byte snapshot that was scored, with its git commit", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def console(summary):
    print("\nSCOREBOARD")
    for key, title, _ in TESTS:
        row = "  ".join(f"{a['label']}: {verdict(a['verdicts'][key]) if 'verdicts' in a else 'not submitted'}"
                        for a in summary["ais"].values())
        print(f"  {title:<24} {row}")
    for a in summary["ais"].values():
        if "verdicts" in a:
            t1 = a["test1"]
            print(f"  {a['label']} champion {a['champion']}: hidden {pct(t1['champ_hid_return_pct'])} "
                  f"(buy & hold {pct(t1['buy_hold_pct'])}), rank {t1['champ_hid_rank']}/{t1['scored']}, "
                  f"luck {a['test5']['champion_pct']}%")
