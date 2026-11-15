"""Builds the one-page visual summary (exam/out/summary_page.html) from exam/out/summary.json and scores_*.csv.

Usage: python exam/make_summary_page.py      (run exam/run_exam.py first)
The page references spaghetti_fable.png and full_history.png, which sit next to it in exam/out/.
"""
import html
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)

import pandas as pd

from report import TESTS, final_verdict

S = json.load(open(os.path.join(OUT, "summary.json")))
E = html.escape


def pct(x, d=2):
    return f"{x:+,.{d}f}%".replace("-", "−")


def money(ret_pct):
    return f"${10000 * (1 + ret_pct / 100):,.0f}"


def pill(state):
    if state is None:
        return '<span class="pill none">not submitted</span>'
    return ('<span class="pill pass"><span aria-hidden="true">✓</span> Pass</span>' if state
            else '<span class="pill fail"><span aria-hidden="true">✕</span> Fail</span>')


def scatter(t, champ, best):
    """Sharpe before (x) against Sharpe in the hidden year (y), one dot per strategy."""
    import math
    x0 = math.floor((t["is_sharpe"].min() - 0.05) / 0.2) * 0.2
    x1 = math.ceil((t["is_sharpe"].max() + 0.05) / 0.2) * 0.2
    y0 = math.floor((t["hid_sharpe"].min() - 0.1) / 0.5) * 0.5
    y1 = math.ceil((t["hid_sharpe"].max() + 0.1) / 0.5) * 0.5
    px = lambda v: (v - x0) / (x1 - x0) * 100
    py = lambda v: (v - y0) / (y1 - y0) * 100
    parts = []
    for v in [y0 + 0.5 * i for i in range(int(round((y1 - y0) / 0.5)) + 1)]:
        parts.append(f'<i class="gl h{" zero" if abs(v) < 1e-9 else ""}" style="bottom:{py(v):.2f}%"></i>'
                     f'<span class="tk y" style="bottom:{py(v):.2f}%">{f"{v:.1f}".replace("-", "−")}</span>')
    for v in [round(x0 + 0.2 * i, 1) for i in range(1, int(round((x1 - x0) / 0.2)) + 1)]:
        parts.append(f'<i class="gl v" style="left:{px(v):.2f}%"></i><span class="tk x" style="left:{px(v):.2f}%">{v:.1f}</span>')
    for _, r in t.sort_values("id").iterrows():
        cls = "dot" + (" champ" if r["id"] == champ else " best" if r["id"] == best else "")
        tip = (f"{r['id']} {r['name']}|Before: Sharpe {r['is_sharpe']:.2f}, rank {int(r['is_rank'])}"
               f"|Hidden year: Sharpe {r['hid_sharpe']:.2f}, {pct(r['hid_net_return_pct'], 1)}, rank {int(r['hid_rank'])}")
        parts.append(f'<b class="{cls}" tabindex="0" data-tip="{E(tip)}" style="left:{px(r["is_sharpe"]):.2f}%;bottom:{py(r["hid_sharpe"]):.2f}%"></b>')
    for sid, text, side in ((champ, "picked as champion", "left"), (best, "best in the hidden year", "right")):
        r = t[t["id"] == sid].iloc[0]
        parts.append(f'<span class="lab {side}" style="left:{px(r["is_sharpe"]):.2f}%;bottom:{py(r["hid_sharpe"]):.2f}%">'
                     f'<strong>{sid}</strong> {text}</span>')
    return ('<div class="plotwrap"><div class="ylab">Sharpe in the hidden year</div>'
            f'<div class="plot scatter">{"".join(parts)}</div>'
            '<div class="xlab">Sharpe before the hidden year (what the AI could see)</div></div>')


def histogram(t, champ_pct):
    bins = [0] * 20
    for v in t["luck_pct"]:
        bins[min(int(v // 5), 19)] += 1
    top = max(bins)
    cols = []
    for i, n in enumerate(bins):
        lo, hi = i * 5, i * 5 + 5
        cols.append(f'<div class="col" tabindex="0" data-tip="{n} strateg{"y" if n == 1 else "ies"}|beat {lo}% to {hi}% of their random twins">'
                    f'<span class="n">{n if n else ""}</span><i class="bar{" over" if lo >= 95 else ""}" style="height:{n / top * 100:.1f}%"></i></div>')
    ticks = "".join(f'<span style="left:{v}%">{v}%</span>' for v in (0, 25, 50, 75, 100))
    return (f'<div class="hist"><div class="cols">{"".join(cols)}'
            f'<i class="need" style="left:95%"><span>95% needed</span></i>'
            f'<i class="mark" style="left:{champ_pct}%"><span>champion {champ_pct:.0f}%</span></i></div>'
            f'<div class="hticks">{ticks}</div><div class="xlab">Share of random twins the strategy beat</div></div>')


def hbars(rows, lo, hi, ref=None):
    """rows: (label, value). Horizontal bars on one zero-based scale."""
    zero = (0 - lo) / (hi - lo) * 100
    out = []
    for label, v in rows:
        w = abs(v) / (hi - lo) * 100
        left = zero if v >= 0 else zero - w
        out.append(f'<div class="hrow"><span class="hl">{label}</span><div class="track" tabindex="0" data-tip="{E(label.replace("<span>", "").replace("</span>", ""))}|{pct(v)} in the hidden year">'
                   f'<i class="zero" style="left:{zero:.2f}%"></i>'
                   + (f'<i class="ref" style="left:{(ref - lo) / (hi - lo) * 100:.2f}%"></i>' if ref is not None else "")
                   + f'<i class="hbar{" neg" if v < 0 else ""}" style="left:{left:.2f}%;width:{max(w, 0.4):.2f}%"></i></div>'
                   f'<span class="hv">{pct(v)}</span></div>')
    return f'<div class="hbars">{"".join(out)}</div>'


def build():
    ais = S["ais"]
    f = ais["fable"]
    done = [a for a in ais.values() if "verdicts" in a]
    t1, t2, t3, t4, t5, b = f["test1"], f["test2"], f["test3"], f["test4"], f["test5"], f["should_have_picked"]
    t = pd.read_csv(os.path.join(OUT, "scores_fable.csv"))
    t = t[t["scored"]]
    champ = f["champion"]
    n_pass = sum(f["verdicts"].values())
    missing = [a["label"] for a in ais.values() if "verdicts" not in a]

    rows = []
    for key, title, rule in TESTS:
        cells = "".join(f"<td>{pill(a['verdicts'][key] if 'verdicts' in a else None)}</td>" for a in ais.values())
        rows.append(f"<tr><th scope=\"row\">{title[3:]}<small>{rule[0].upper() + rule[1:]}.</small></th>{cells}</tr>")
    heads = "".join(f'<th scope="col"><i class="sw {k}"></i>{a["label"]}</th>' for k, a in ais.items())
    totals = "".join(f"<td><strong>{sum(a['verdicts'].values())} of 5</strong></td>" if "verdicts" in a else "<td>–</td>" for a in ais.values())
    board = (f'<div class="scroll"><table class="board"><thead><tr><th scope="col">Test</th>{heads}</tr></thead>'
             f'<tbody>{"".join(rows)}<tr class="total"><th scope="row">Tests passed</th>{totals}</tr></tbody></table></div>')

    tweak_rows = [(f"{r['param']} <span>{r['from']} → {r['to']}</span>", r["hid_return_pct"]) for r in t2["versions"]]
    fee_rows = [(name, t3[k]) for k, name in (("0", "No fees"), ("1", "Normal fees"), ("2", "Double fees"), ("3", "Triple fees"))]

    checks = "".join(
        f'<li><span class="pill {"pass" if c["verdict"] == "CLEAN" else "fail"}"><span aria-hidden="true">{"✓" if c["verdict"] == "CLEAN" else "!"}</span> '
        f'{"Clean" if c["verdict"] == "CLEAN" else "Problem"}</span><div><strong>{E(c["check"].split(" (~")[0])}</strong><small>{E(c["detail"])}</small></div></li>'
        for c in S["cheat_checks"])
    proof = "".join(f'<tr><th scope="row">{E(p["check"])}</th><td>{p["expected"]}</td><td>{p["got"]}</td>'
                    f'<td>{pill(p["result"] == "MATCH").replace("Pass", "Match").replace("Fail", "No match")}</td></tr>' for p in S["proof"])
    d = S["proof_diagnostic"]
    n_match = sum(p["result"] == "MATCH" for p in S["proof"])
    fam = "".join(f'<tr><th scope="row">{E(r["family"])}</th><td>{r["n"]}</td><td>{r["profitable"]}</td><td>{pct(r["median_hid_return"], 1)}</td>'
                  f'<td>{r["median_hid_sharpe"]:.2f}</td></tr>' for r in sorted(f["by_family"], key=lambda r: -r["median_hid_sharpe"]))
    top = "".join(
        f'<tr{" class=\"is-champ\"" if r["id"] == champ else ""}><td>{i}</td><th scope="row">{r["id"]} {E(r["name"])}</th><td>{int(r["is_rank"])}</td>'
        f'<td>{pct(r["hid_net_return_pct"], 1)}</td><td>{r["hid_sharpe"]:.2f}</td><td>{pct(r["hid_max_drawdown_pct"], 1)}</td><td>{r["luck_pct"]:.0f}%</td></tr>'
        for i, r in enumerate(f["hidden_top10"], 1))

    lead = (f"Two AIs were each asked for 100 bitcoin trading strategies. Only {done[0]['label']} handed any in, so there is no "
            f"head-to-head winner. {done[0]['label']}'s champion made money in a year when bitcoin lost {abs(t1['buy_hold_pct']):.0f}%, "
            f"but it passed only {n_pass} of the 5 tests.") if missing else "Both AIs handed in 100 strategies."

    bk = f["basket"]
    label, why = final_verdict(f)
    lead = (f"Fable built {t1['scored']} bitcoin trading strategies on prices up to October 2025. Here they are run, untouched, on the "
            f"following year. In short: {why}.")
    rows = "".join(
        f'<tr><th scope="row">{title[3:]}<small>It {rule}.</small></th><td>{pill(f["verdicts"][key])}</td><td>{pill(bk["verdicts"][key])}</td></tr>'
        for key, title, rule in TESTS)
    board = ('<div class="scroll"><table class="board"><thead><tr><th scope="col">Test</th>'
             f'<th scope="col"><i class="sw fable"></i>Champion {champ}</th><th scope="col"><i class="sw basket"></i>All {bk["n"]} as one basket</th></tr></thead>'
             f'<tbody>{rows}<tr class="total"><th scope="row">Tests passed</th><td><strong>{n_pass} of 5</strong></td>'
             f'<td><strong>{sum(bk["verdicts"].values())} of 5</strong></td></tr></tbody></table></div>')
    bk_fees = [(name, bk["fees"][k]) for k, name in (("0", "No fees"), ("1", "Normal fees"), ("2", "Double fees"), ("3", "Triple fees"))]
    bk_tweaks = [(f"All settings <span>\u00d7{tw['mult']}</span>", tw["hid_return_pct"]) for tw in bk["tweaks"]]
    meters = "".join(
        f'<div class="hrow"><span class="hl">{name}</span><div class="track" tabindex="0" data-tip="{name}|beat {v:.1f}% of its randomly timed twins">'
        f'<i class="ref" style="left:95%"></i><i class="hbar{cls}" style="left:0;width:{v:.1f}%"></i></div><span class="hv">{v:.0f}%</span></div>'
        for name, v, cls in ((f"Basket of {bk['n']}", bk["luck_pct"], " basket"), (f"Champion {champ}", t5["champion_pct"], "")))

    return f"""<meta name="claude:viewport-fit-sides" content="cover">
<title>Hidden-Year Exam</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap">
<style>
/* Layout: one reading column that scrolls like a story; verdict first, evidence after. Single dark look to match the exam charts. */
:root {{
  color-scheme: dark;
  --bg: #0B0F19; --surface: #121826; --line: #232B3B; --text: #E8EBF1; --muted: #9AA3B2; --faint: #6B7484;
  --fable: #F59E0B; --opus: #8B5CF6; --btc: #9CA3AF; --good: #34D399; --bad: #F87171;
  --good-bg: rgba(52,211,153,.13); --bad-bg: rgba(248,113,113,.13);
  --display: "Space Grotesk", "Segoe UI", system-ui, sans-serif; --body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--text); font: 16px/1.6 var(--body); margin: 0; }}
main {{ max-width: 1040px; margin: 0 auto; padding-block: 40px 72px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: flex; flex-direction: column; gap: 56px; overflow-x: clip; }}
section {{ display: flex; flex-direction: column; gap: 18px; min-width: 0; }}
h1, h2, h3 {{ font-family: var(--display); text-wrap: balance; margin: 0; line-height: 1.15; }}
h1 {{ font-size: clamp(2.2rem, 6vw, 3.6rem); font-weight: 700; letter-spacing: -.02em; }}
h2 {{ font-size: clamp(1.4rem, 3.4vw, 1.9rem); font-weight: 600; }}
h3 {{ font-size: 1.08rem; font-weight: 600; }}
p {{ margin: 0; max-width: 68ch; }}
.eyebrow {{ font-size: .78rem; letter-spacing: .09em; text-transform: uppercase; color: var(--muted); }}
.lead {{ font-size: 1.18rem; color: var(--text); }}
.muted, small {{ color: var(--muted); }}
small {{ display: block; font-size: .86rem; line-height: 1.45; font-weight: 400; }}
strong {{ font-weight: 600; }}
.num {{ font-variant-numeric: tabular-nums; }}
.stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; border-block: 1px solid var(--line); }}
.stat {{ padding: 18px 16px 18px 0; display: flex; flex-direction: column; gap: 4px; min-width: 0; }}
.stat + .stat {{ padding-left: 16px; border-left: 1px solid var(--line); }}
.stat .v {{ font: 700 clamp(1.7rem, 4vw, 2.4rem)/1.05 var(--display); font-variant-numeric: tabular-nums; }}
.stat .k {{ font-size: .86rem; color: var(--muted); line-height: 1.4; }}
.sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 7px; }}
.sw.basket {{ background: var(--text); }}
.result {{ display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; font: 700 clamp(1.3rem, 3.6vw, 1.9rem)/1.2 var(--display); letter-spacing: .01em; }}
.result .eyebrow {{ font-family: var(--body); font-weight: 500; }}
.hbar.basket {{ background: var(--text); }}
ol.steps {{ margin: 0; padding-left: 1.3em; display: flex; flex-direction: column; gap: 8px; max-width: 72ch; }}
.sw.fable {{ background: var(--fable); }} .sw.opus {{ background: var(--opus); }} .sw.btc {{ background: var(--btc); }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 11px 14px 11px 0; border-bottom: 1px solid var(--line); vertical-align: top; font-weight: 400; }}
thead th {{ font-size: .78rem; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
tbody th {{ font-weight: 500; }}
td {{ white-space: nowrap; }}
.board tbody th {{ min-width: 220px; }}
.total th, .total td {{ border-bottom: 0; font-family: var(--display); }}
tr.is-champ th, tr.is-champ td {{ background: rgba(245,158,11,.09); }}
.pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px; font-size: .84rem; font-weight: 600; white-space: nowrap; }}
.pill.pass {{ background: var(--good-bg); color: var(--good); }} .pill.fail {{ background: var(--bad-bg); color: var(--bad); }}
.pill.none {{ border: 1px dashed var(--line); color: var(--faint); font-weight: 500; }}
figure {{ margin: 0; display: flex; flex-direction: column; gap: 8px; }}
figure img {{ width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--line); display: block; }}
figcaption {{ font-size: .86rem; color: var(--muted); }}
.two {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 36px 40px; }}
.block {{ display: flex; flex-direction: column; gap: 12px; min-width: 0; }}
.verdict {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
/* scatter */
.plotwrap {{ display: flex; flex-direction: column; gap: 6px; }}
.ylab, .xlab {{ font-size: .8rem; color: var(--muted); }}
.xlab {{ text-align: center; padding-top: 22px; }}
.plot {{ position: relative; margin: 6px 12px 0 34px; aspect-ratio: 16 / 10; min-height: 300px; border-left: 1px solid var(--line); border-bottom: 1px solid var(--line); }}
.gl {{ position: absolute; background: var(--line); opacity: .7; }}
.gl.h {{ left: 0; right: 0; height: 1px; }} .gl.v {{ top: 0; bottom: 0; width: 1px; }}
.gl.zero {{ background: var(--muted); opacity: .8; }}
.tk {{ position: absolute; font-size: .74rem; color: var(--muted); font-variant-numeric: tabular-nums; }}
.tk.y {{ left: -34px; width: 28px; text-align: right; transform: translateY(50%); }} .tk.x {{ bottom: -22px; transform: translateX(-50%); }}
.dot {{ position: absolute; width: 10px; height: 10px; margin: 0 0 -5px -5px; border-radius: 50%; background: var(--fable); opacity: .6; box-shadow: 0 0 0 2px var(--bg); cursor: default; }}
.dot:hover, .dot:focus-visible {{ opacity: 1; outline: 2px solid var(--text); outline-offset: 1px; z-index: 3; }}
.dot.champ, .dot.best {{ opacity: 1; width: 16px; height: 16px; margin: 0 0 -8px -8px; box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--text); z-index: 2; }}
.dot.best {{ background: var(--text); box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--fable); }}
.lab {{ position: absolute; font-size: .8rem; color: var(--text); white-space: nowrap; z-index: 2; pointer-events: none; }}
.lab.left {{ transform: translate(16px, 50%); }} .lab.right {{ transform: translate(16px, 50%); }}
/* histogram */
.hist {{ display: flex; flex-direction: column; }}
.cols {{ position: relative; display: flex; align-items: flex-end; gap: 2px; height: 190px; border-bottom: 1px solid var(--line); padding-top: 34px; }}
.col {{ flex: 1; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 3px; min-width: 0; }}
.col .n {{ font-size: .68rem; color: var(--muted); font-variant-numeric: tabular-nums; }}
.bar {{ display: block; width: 100%; background: var(--fable); opacity: .55; border-radius: 4px 4px 0 0; }}
.bar.over {{ opacity: 1; }}
.col:hover .bar, .col:focus-visible .bar {{ opacity: 1; }} .col:focus-visible {{ outline: 2px solid var(--text); }}
.need, .mark {{ position: absolute; top: 0; bottom: 0; width: 0; border-left: 1px dashed var(--muted); pointer-events: none; }}
.mark {{ border-left: 2px solid var(--text); top: 14px; }}
.need span, .mark span {{ position: absolute; top: 0; right: 6px; font-size: .74rem; color: var(--muted); white-space: nowrap; font-style: normal; }}
.mark span {{ color: var(--text); top: -2px; }}
.hticks {{ position: relative; height: 20px; }}
.hticks span {{ position: absolute; top: 4px; transform: translateX(-50%); font-size: .74rem; color: var(--muted); }}
.hticks span:first-child {{ transform: none; }} .hticks span:last-child {{ transform: translateX(-100%); }}
.hist .xlab {{ padding-top: 4px; }}
/* horizontal bars */
.hbars {{ display: flex; flex-direction: column; gap: 8px; }}
.hrow {{ display: grid; grid-template-columns: 118px minmax(0, 1fr) 74px; align-items: center; gap: 10px; font-size: .86rem; }}
.hl {{ color: var(--text); white-space: nowrap; }} .hl span {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
.hv {{ text-align: right; font-variant-numeric: tabular-nums; }}
.track {{ position: relative; height: 18px; }}
.track:focus-visible {{ outline: 2px solid var(--text); outline-offset: 2px; }}
.hbar {{ position: absolute; top: 2px; bottom: 2px; background: var(--fable); border-radius: 0 4px 4px 0; }}
.hbar.neg {{ border-radius: 4px 0 0 4px; opacity: .55; }}
.zero {{ position: absolute; top: -3px; bottom: -3px; width: 1px; background: var(--muted); }}
.ref {{ position: absolute; top: -3px; bottom: -3px; width: 0; border-left: 1px dashed var(--text); opacity: .7; }}
.legend {{ display: flex; gap: 18px; flex-wrap: wrap; font-size: .8rem; color: var(--muted); }}
.legend i {{ display: inline-block; vertical-align: middle; margin-right: 6px; }}
.legend .lz {{ width: 0; height: 14px; border-left: 1px dashed var(--text); }}
.duo {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; border-block: 1px solid var(--line); }}
.duo > div {{ padding: 18px 20px 18px 0; display: flex; flex-direction: column; gap: 6px; }}
.duo > div + div {{ padding-left: 20px; border-left: 1px solid var(--line); }}
.duo .v {{ font: 700 2rem/1.1 var(--display); font-variant-numeric: tabular-nums; }}
.checks {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }}
.checks .pill {{ justify-self: start; }}
.checks li {{ display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 14px; padding: 12px 0; border-bottom: 1px solid var(--line); align-items: start; }}
.notes {{ margin: 0; padding-left: 1.2em; display: flex; flex-direction: column; gap: 10px; max-width: 72ch; }}
code {{ font: .88em ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--text); background: var(--surface); padding: 1px 5px; border-radius: 4px; }}
#tip {{ position: fixed; z-index: 20; pointer-events: none; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; font-size: .8rem; line-height: 1.45; max-width: 280px; box-shadow: 0 8px 24px rgba(0,0,0,.45); }}
#tip b {{ display: block; font-weight: 600; }} #tip span {{ display: block; color: var(--muted); }}
@media (max-width: 760px) {{
  main {{ gap: 44px; padding-block: 28px 56px; }}
  .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .stat {{ padding: 14px 12px 14px 0; }} .stat:nth-child(3) {{ padding-left: 0; border-left: 0; }}
  .stat:nth-child(n+3) {{ border-top: 1px solid var(--line); }}
  .two, .duo {{ grid-template-columns: minmax(0, 1fr); }}
  .duo > div + div {{ padding-left: 0; border-left: 0; border-top: 1px solid var(--line); }}
  .hrow {{ grid-template-columns: 104px minmax(0, 1fr) 66px; gap: 8px; }}
  .lab {{ font-size: .72rem; }}
  .lab.left {{ transform: translate(calc(-100% - 14px), 50%); }}
  .checks li {{ grid-template-columns: minmax(0, 1fr); gap: 6px; }}
}}
</style>

<main>
<header>
  <section>
    <p class="eyebrow">BTCUSDT perpetual &middot; 4-hour candles &middot; hidden year {S['hidden_from'][:10]} to {S['hidden_to'][:10]}</p>
    <h1>Hidden-Year Exam</h1>
    <p class="result"><span class="eyebrow">Result</span>{label.capitalize()}</p>
    <p class="lead">{lead}</p>
    <div class="stats">
      <div class="stat"><span class="v">{money(t1['champ_hid_return_pct'])}</span><span class="k"><i class="sw fable"></i>The champion Fable named in advance, {champ}, from $10,000 ({pct(t1['champ_hid_return_pct'])})</span></div>
      <div class="stat"><span class="v">{money(t1['buy_hold_pct'])}</span><span class="k"><i class="sw btc"></i>Just holding bitcoin, from $10,000 ({pct(t1['buy_hold_pct'])})</span></div>
      <div class="stat"><span class="v">{money(bk['hidden']['net_return_pct'])}</span><span class="k"><i class="sw basket"></i>All {bk['n']} strategies as one basket, from $10,000 ({pct(bk['hidden']['net_return_pct'])})</span></div>
      <div class="stat"><span class="v">{bk['luck_pct']:.0f}%</span><span class="k">Random look-alikes the basket beat. 95% is needed to rule out luck</span></div>
    </div>
  </section>
</header>

<section>
  <h2>Scoreboard</h2>
  {board}
  <p class="muted">The champion's pass lines were fixed before any strategy was scored. The basket column asks the same five questions of all {bk['n']} strategies held together; those versions were added after the champion's results were known.</p>
</section>

<section>
  <h2>All 100 strategies in the hidden year</h2>
  <figure><img src="spaghetti_fable.png" alt="Equity of each of Fable's 100 strategies over the hidden year from $10,000, with the champion in amber, the equal-weight basket in white and bitcoin buy and hold as a dashed grey line that ends near $7,056.">
  <figcaption>Each thin line is one strategy starting with $10,000. Thick amber: the champion. White: all 100 as one basket. Dashed grey: holding bitcoin.</figcaption></figure>
  <p>{t1['profitable']} of {t1['scored']} strategies ended above $10,000 and {t1['beat_buy_hold']} beat holding bitcoin. Most of these rules can bet on falling prices, and the hidden year was a falling market, so this result says less than it seems to. The luck check further down is the fairer test.</p>
</section>

<section>
  <h2>Past results did not predict the hidden year</h2>
  <p>Each dot is one strategy. If a good score on the old data meant a good score on new data, the dots would climb from bottom left to top right. They do not: the rank link is {f"{t1['spearman']:+.2f}".replace('-', '−')}, where 0 means no link at all.</p>
  {scatter(t, champ, b['id'])}
  <div class="duo">
    <div><span class="eyebrow">What Fable picked</span><span class="v">{pct(t1['champ_hid_return_pct'], 1)}</span>
      <span><strong>{champ} {E(f['champion_name'])}</strong></span>
      <small>Ranked {t1['champ_is_rank']} of {t1['scored']} before the hidden year, {t1['champ_hid_rank']} of {t1['scored']} in it. Worst dip {pct(t1['champ_hid_max_dd_pct'], 1)}, {t1['champ_hid_trades']} trades.</small></div>
    <div><span class="eyebrow">What it should have picked</span><span class="v">{pct(b['hid_return_pct'], 1)}</span>
      <span><strong>{b['id']} {E(b['name'])}</strong></span>
      <small>Ranked {b['is_rank']} of {b['of']} before the hidden year, 1 of {b['of']} in it. Worst dip {pct(b['hid_max_dd_pct'], 1)}, {b['hid_trades']} trades. Nothing in the old data pointed to it.</small></div>
  </div>
</section>

<section>
  <h2>The champion under stress</h2>
  <div class="two">
    <div class="block">
      <div class="verdict"><h3>Tweak the settings</h3>{pill(f['verdicts']['test2'])}</div>
      <p class="muted">Each setting moved 20% down or up, one at a time. {t2['profitable']} of {t2['total']} versions still made money.</p>
      {hbars(tweak_rows, -10, 40, ref=t1['champ_hid_return_pct'])}
      <div class="legend"><span><i class="lz"></i>champion as submitted ({pct(t1['champ_hid_return_pct'], 1)})</span></div>
    </div>
    <div class="block">
      <div class="verdict"><h3>Higher fees</h3>{pill(f['verdicts']['test3'])}</div>
      <p class="muted">The same hidden year with trading costs removed, doubled and tripled.</p>
      {hbars(fee_rows, -10, 40)}
    </div>
    <div class="block">
      <div class="verdict"><h3>Worst case</h3>{pill(f['verdicts']['test4'])}</div>
      <p class="muted">The champion's {t4['trades']} hidden-year trades, reshuffled 1,000 times.</p>
      <div class="scroll"><table><tbody>
        <tr><th scope="row">Reshuffles that lost money</th><td>{t4['pct_below_zero']:.1f}%</td></tr>
        <tr><th scope="row">Typical worst dip</th><td>{pct(t4['median_max_dd_pct'], 1)}</td></tr>
        <tr><th scope="row">Worst dip in the unluckiest 5%</th><td>{pct(t4['p5_max_dd_pct'], 1)}</td></tr>
      </tbody></table></div>
    </div>
    <div class="block">
      <div class="verdict"><h3>Luck check</h3>{pill(f['verdicts']['test5'])}</div>
      <p class="muted">Every strategy against 1,000 random twins: same trades, same direction, same length, random timing.</p>
      {histogram(t, t5['champion_pct'])}
    </div>
  </div>
  <p>The champion beat {t5['champion_pct']:.0f}% of its twins. That is better than a coin flip but short of the 95% needed to call it skill. The typical strategy beat {t5['median_pct']:.0f}%, and only {t5['passed']} of {t5['of']} cleared the bar.</p>
</section>

<section>
  <h2>All {bk['n']} strategies as one basket</h2>
  <p>Hold every strategy at once with equal money in each. In practice that is one position equal to the average of the {bk['n']} signals. No picking is involved, so hindsight cannot flatter it.</p>
  <div class="duo">
    <div><span class="eyebrow">Before the hidden year</span><span class="v">Sharpe {bk['before']['sharpe']:.2f}</span>
      <small>{pct(bk['before']['cagr_pct'], 1)} a year, worst dip {pct(bk['before']['max_drawdown_pct'], 1)}.</small></div>
    <div><span class="eyebrow">Hidden year</span><span class="v">Sharpe {bk['hidden']['sharpe']:.2f}</span>
      <small>{pct(bk['hidden']['net_return_pct'], 1)}, worst dip {pct(bk['hidden']['max_drawdown_pct'], 1)}. The group behaved on new data the way it did on old data.</small></div>
  </div>
  <div class="two">
    <div class="block">
      <div class="verdict"><h3>Tweak the settings</h3>{pill(bk['verdicts']['test2'])}</div>
      <p class="muted">Every numeric setting of every strategy moved 20% down, then 20% up, all at once.</p>
      {hbars(bk_tweaks, -10, 40, ref=bk['hidden']['net_return_pct'])}
      <div class="legend"><span><i class="lz"></i>basket as submitted ({pct(bk['hidden']['net_return_pct'], 1)})</span></div>
    </div>
    <div class="block">
      <div class="verdict"><h3>Higher fees</h3>{pill(bk['verdicts']['test3'])}</div>
      <p class="muted">Trading costs removed, doubled and tripled.</p>
      {hbars(bk_fees, -10, 40)}
    </div>
    <div class="block">
      <div class="verdict"><h3>Worst case</h3>{pill(bk['verdicts']['test4'])}</div>
      <p class="muted">The basket's hidden year cut into {bk['worst_case']['weeks']} weeks, reshuffled 1,000 times.</p>
      <div class="scroll"><table><tbody>
        <tr><th scope="row">Reshuffles that lost money</th><td>{bk['worst_case']['pct_below_zero']:.1f}%</td></tr>
        <tr><th scope="row">Typical worst dip</th><td>{pct(bk['worst_case']['median_max_dd_pct'], 1)}</td></tr>
        <tr><th scope="row">Worst dip in the unluckiest 5%</th><td>{pct(bk['worst_case']['p5_max_dd_pct'], 1)}</td></tr>
      </tbody></table></div>
    </div>
    <div class="block">
      <div class="verdict"><h3>Luck check</h3>{pill(bk['verdicts']['test5'])}</div>
      <p class="muted">The basket's own positions slid to 1,000 random other moments of the year. Same size, same rhythm, different timing.</p>
      <div class="hbars">{meters}</div>
      <div class="legend"><span><i class="lz"></i>95% needed to rule out luck</span></div>
    </div>
  </div>
  <p>The basket beat {bk['luck_pct']:.0f}% of its randomly timed twins, which typically made {pct(bk['twin_median_return_pct'], 1)}. That points to real timing value, but it is short of the 95% line. The {bk['n']} strategies also move together (typical correlation {bk['median_pair_corr_hidden']:.2f}), so this is one bet, not {bk['n']}.</p>
</section>

<section>
  <h2>What to push forward</h2>
  <p><strong>The basket of all {bk['n']}, not a single strategy.</strong> {b['id']} made {pct(b['hid_return_pct'], 1)} but ranked {b['is_rank']} of {b['of']} beforehand, so choosing it now is picking the lottery winner after the draw. The champion {champ} was the honest advance pick and failed three tests.</p>
  <ol class="steps">
    <li>Freeze the {bk['n']} files as they are. No re-tuning on the hidden year.</li>
    <li>Trade the basket on paper for 3 to 6 months on live 4-hour candles. Only data from today on is truly unseen by the model.</li>
    <li>Add funding costs. The backtester charges fees and slippage but not the funding payments of perpetual futures.</li>
    <li>Fix the stop rule now, for example: drop it if the forward Sharpe is below 0.5 or the dip passes 25%.</li>
    <li>Consider small real money only after that.</li>
  </ol>
</section>

<section>
  <h2>Best ten in the hidden year</h2>
  <div class="scroll"><table><thead><tr><th>#</th><th>Strategy</th><th>Rank before</th><th>Return</th><th>Sharpe</th><th>Worst dip</th><th>Beat twins</th></tr></thead><tbody>{top}</tbody></table></div>
  <h3>By family</h3>
  <div class="scroll"><table><thead><tr><th>Family</th><th>Strategies</th><th>Made money</th><th>Median return</th><th>Median Sharpe</th></tr></thead><tbody>{fam}</tbody></table></div>
  <p class="muted">Sharpe is return per unit of bumpiness: above 1 is good, near 0 is nothing. The champion sits at rank {t1['champ_hid_rank']}, so it is not in this table.</p>
</section>

<section>
  <h2>Since April 2020</h2>
  <figure><img src="full_history.png" alt="Fable's champion, the basket of all 100 strategies and bitcoin buy and hold from April 2020 on a log scale, all starting at $10,000, with the hidden year shaded purple.">
  <figcaption>$10,000 start, log scale. Amber: the champion. White: the basket. The shaded band is the hidden year.</figcaption></figure>
</section>

<section>
  <h2>Did anybody cheat?</h2>
  <ul class="checks">{checks}</ul>
  <p>The session logs the spec asks for are not on this machine, because Fable's strategies were built in a separate cloud session. As a substitute, all 38 tool calls of that session were read through the session history. What they show:</p>
  <ul class="notes">
    <li><strong>No access to the hidden file.</strong> No command or path touches <code>hidden/</code>, there are no web requests, no downloads and no dates after October 2025. The only price file read was the in-sample one.</li>
    <li><strong>The folder lock did not apply.</strong> The session started in the project root instead of inside <code>fable/</code>. It listed every file name in the repository, so it saw that <code>hidden/</code> exists, and it called one connector tool that only lists folder names.</li>
    <li><strong>The hidden year is not fully unknown to the AI.</strong> Its own FINAL.md says its training data runs past October 2025 and that it has a rough idea how bitcoin moved afterwards. It never saw the hidden candles, but that background knowledge cannot be ruled out as an influence.</li>
    <li><strong>This exam session also built the exam room,</strong> downloaded the hidden file, and started a Fable build of its own that was interrupted. None of that work was used: the 100 scored strategies come byte for byte from the other session's commit.</li>
  </ul>
</section>

<section>
  <h2>Is the engine right?</h2>
  <div class="scroll"><table><thead><tr><th>Reference check</th><th>Expected</th><th>Got</th><th>Result</th></tr></thead><tbody>{proof}</tbody></table></div>
  <p>{n_match} of {len(S['proof'])} reference numbers match exactly. The rest could not be matched by changing code. The likely cause is the price feed: on {d['bar'][:10]} the Binance close stopped {d['gap_pct']}% (about ${d['gap_usd']:,.0f}) short of the line where Rule B flips. Treat that one candle as crossed and Rule B gives {pct(d['if_crossed_return_pct'])} with {d['if_crossed_trades']} trades, against the reference +26.15% and 26.</p>
  <p class="muted">Full numbers: <code>exam/RESULTS.md</code>, <code>exam/out/scores_fable.csv</code>. Re-run with <code>python exam/run_exam.py</code>.</p>
</section>
</main>

<div id="tip" hidden></div>
<script>
(function () {{
  var tip = document.getElementById('tip');
  function show(el, x, y) {{
    var parts = el.getAttribute('data-tip').split('|');
    tip.textContent = '';
    parts.forEach(function (p, i) {{ var n = document.createElement(i ? 'span' : 'b'); n.textContent = p; tip.appendChild(n); }});
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.max(8, Math.min(x + 14, window.innerWidth - w - 8)) + 'px';
    tip.style.top = (y + h + 22 > window.innerHeight ? y - h - 12 : y + 16) + 'px';
  }}
  document.querySelectorAll('[data-tip]').forEach(function (el) {{
    el.addEventListener('pointermove', function (e) {{ show(el, e.clientX, e.clientY); }});
    el.addEventListener('pointerleave', function () {{ tip.hidden = true; }});
    el.addEventListener('focus', function () {{ var r = el.getBoundingClientRect(); show(el, r.left + r.width / 2, r.bottom); }});
    el.addEventListener('blur', function () {{ tip.hidden = true; }});
  }});
}})();
</script>
"""


if __name__ == "__main__":
    path = os.path.join(OUT, "summary_page.html")
    open(path, "w", encoding="utf-8").write(build())
    print("wrote", os.path.relpath(path), f"({os.path.getsize(path):,} bytes)")
