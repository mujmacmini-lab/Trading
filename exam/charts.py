"""STEP 5 - charts (dark background, Fable #F59E0B, Opus #8B5CF6, BTC grey dashed)."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from engine import CUT

BG, FG, GRID, BTC, SHADE = "#0B0F19", "#E5E7EB", "#1F2937", "#9CA3AF", "#8B5CF6"
START = 10_000


def _style(ax, title, subtitle):
    ax.set_facecolor(BG)
    ax.figure.set_facecolor(BG)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=FG, labelsize=10)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"\\${v:,.0f}"))
    ax.set_title(title, color=FG, fontsize=15, fontweight="bold", loc="left", pad=26)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=BTC, fontsize=10.5, va="bottom")


def spaghetti(ai, meta, res, full, out):
    h = full.index >= CUT
    close = full["close"][h]
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=160)
    champ = res["champion"]
    n_up = 0
    for sid, r in res["runs"].items():
        eq = START * (1 + r["net"][h]).cumprod()
        n_up += eq.iloc[-1] > START
        if sid != champ:
            ax.plot(eq.index, eq.values, color=meta["color"], alpha=0.22, linewidth=0.8)
    bh = START * close / close.iloc[0]
    ax.plot(bh.index, bh.values, color=BTC, linestyle="--", linewidth=1.8, label=f"BTC buy & hold  \\${bh.iloc[-1]:,.0f}")
    if champ in res["runs"]:
        eq = START * (1 + res["runs"][champ]["net"][h]).cumprod()
        ax.plot(eq.index, eq.values, color=meta["color"], linewidth=2.8, label=f"Champion {champ}  \\${eq.iloc[-1]:,.0f}")
    if res.get("basket_net") is not None:
        eq = START * (1 + res["basket_net"][h]).cumprod()
        ax.plot(eq.index, eq.values, color=FG, linewidth=2.2, label=f"All {len(res['runs'])} as one basket  \\${eq.iloc[-1]:,.0f}")
    ax.axhline(START, color=FG, linewidth=0.8, alpha=0.5)
    _style(ax, f"{meta['label']}: all {len(res['runs'])} strategies on the hidden year",
           f"\\$10,000 start, {close.index[0]:%d %b %Y} to {close.index[-1]:%d %b %Y}, fees included.  "
           f"{n_up} of {len(res['runs'])} finished above \\$10,000.")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.legend(loc="upper left", frameon=False, labelcolor=FG, fontsize=11)
    path = os.path.join(out, f"spaghetti_{ai}.png")
    fig.savefig(path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return path


def full_history(results, full, ais, out):
    close = full["close"]
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=160)
    ax.axvspan(CUT, full.index[-1], color=SHADE, alpha=0.16, linewidth=0)
    bh = START * close / close.iloc[0]
    ax.plot(bh.index, bh.values, color=BTC, linestyle="--", linewidth=1.6, label=f"BTC buy & hold  \\${bh.iloc[-1]:,.0f}")
    for ai, meta in ais.items():
        res = results.get(ai)
        if not res or res["champion"] not in res["runs"]:
            continue
        eq = START * (1 + res["runs"][res["champion"]]["net"]).cumprod()
        ax.plot(eq.index, eq.values, color=meta["color"], linewidth=2.2,
                label=f"{meta['label']} champion {res['champion']}  \\${eq.iloc[-1]:,.0f}")
        if res.get("basket_net") is not None:
            eq = START * (1 + res["basket_net"]).cumprod()
            ax.plot(eq.index, eq.values, color=FG, linewidth=1.6,
                    label=f"{meta['label']}: all {len(res['runs'])} as one basket  \\${eq.iloc[-1]:,.0f}")
    ax.set_yscale("log")
    ax.set_yticks([10_000, 20_000, 50_000, 100_000, 200_000])
    missing = [m["label"] for a, m in ais.items() if a not in results]
    _style(ax, "Champion and basket vs bitcoin since April 2020",
           "\\$10,000 start, log scale, fees included. Purple band = hidden year the strategies were not built on.")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"\\${v:,.0f}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    ax.text(CUT, ax.get_ylim()[1], " hidden", color=SHADE, fontsize=11, va="top", ha="left", fontweight="bold")
    ax.legend(loc="upper left", frameon=False, labelcolor=FG, fontsize=11)
    path = os.path.join(out, "full_history.png")
    fig.savefig(path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return path


def make_all(results, full, ais, out):
    made = {}
    for ai, meta in ais.items():
        target = os.path.join(out, f"spaghetti_{ai}.png")
        if ai in results and results[ai]["runs"]:
            made[f"spaghetti_{ai}.png"] = os.path.relpath(spaghetti(ai, meta, results[ai], full, out), out)
        elif os.path.exists(target):
            os.remove(target)
    made["full_history.png"] = os.path.relpath(full_history(results, full, ais, out), out)
    return made
