"""The "get back" chart card: how much of the week's sandwich loss victims recover under per-block clearing.

usage: python scripts/card.py [RESULTS]
reads RESULTS/victims.csv, writes RESULTS/mev-get-back-landscape.png (1024x768 design, 2048x1536 file) and
RESULTS/mev-get-back-square.png (1024x1024 design, 2048x2048 file).
All sizes below are px on a 1024px-wide canvas; the smallest text is MIN_TEXT_PX.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
R = "results"

NAVY, RED, WHITE = "#0b1f4b", "#c8102e", "#ffffff"
AS_OF = "17 Oct 2026"
ATTACKER_LABEL = "Attacker, no slippage limit (arrival)"
MIN_TEXT_PX = 26
W, MARGIN, DPI = 1024, 48, 200

# (label, victims.csv column, accent). Shares equal results/summary.json prevented_share_*.
SCENARIOS = [
    ("Same orders, arrival order", "mech_gain_usd", False),
    ("Same orders, random tie-break (mean of 200)", "mech_gain_mean", False),
    (ATTACKER_LABEL, "mech_gain_attacker_unlimited_usd", True),
    ("Attackers deterred (their orders removed)", "mech_gain_attacker_removed_usd", False),
]


def num(x):
    return float(x) if x not in ("", None) else 0.0


def scenarios(results="results"):
    """Total victim loss and, per scenario, the dollars returned (each victim capped at its own loss)."""
    vic = [y for y in csv.DictReader(open(os.path.join(results, "victims.csv"))) if num(y["loss_a_usd"]) > 0]
    loss = sum(num(y["loss_a_usd"]) for y in vic)
    rows = []
    for label, col, accent in SCENARIOS:
        got = sum(min(max(num(y[col]), 0), num(y["loss_a_usd"])) for y in vic)
        rows.append(dict(label=label, usd=got, share=got / loss, accent=accent))
    return loss, rows


def pct(s):
    return f"{s:.2%}" if s > 0.995 else f"{s:.1%}"


def load_fonts():
    for f in ("RobotoSlab-Bold.ttf", "Archivo-Regular.ttf", "Archivo-SemiBold.ttf"):
        font_manager.fontManager.addfont(os.path.join(HERE, "card-fonts", f))


def draw(path, h, square):
    loss, rows = scenarios(R)
    lo = round(min(r["share"] for r in rows[:3]) * 100)
    hi = round(max(r["share"] for r in rows[:3]) * 100)
    title = [f"Per-block clearing hands victims", f"back {lo}–{hi}% of a week’s",
             f"${loss / 1000:.1f}k sandwich loss"] if square else \
            ["Per-block clearing hands victims back", f"{lo}–{hi}% of a week’s ${loss / 1000:.1f}k sandwich loss"]
    sub = ["Uniswap v3 WETH/USDT 0.01%, 5–11 Oct 2026, 236 sandwiches.",
           f"Dollars returned out of ${loss:,.0f} lost; full bar = full loss."]
    foot = ["Source: Ethereum logs via rpc.mevblocker.io; Chan, Wu & Shi (AFT 2025)", "mechanism replayed on the same blocks.",
            f"Data as of {AS_OF}."]
    tpx, bar_h, lab_gap = (50, 48, 6) if square else (38, 40, 4)

    fig = plt.figure(figsize=(W / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(h, 0)
    ax.axis("off")
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    used = []

    def text(x, y, s, px, family, weight="normal", color=NAVY, ha="left", va="top"):
        assert px >= MIN_TEXT_PX, (s, px)
        t = ax.text(x, y, s, fontsize=px * 0.72, family=family, weight=weight, color=color, ha=ha, va=va)
        bb = t.get_window_extent(rend)
        assert bb.x0 >= MARGIN - 1 and bb.x1 <= W - MARGIN + 1, (s, bb.x0, bb.x1)
        used.append(px)
        return bb.height

    y = 44
    for line in title:
        text(MARGIN, y, line, tpx, "Roboto Slab", "bold")
        y += tpx * 1.25
    y += 16
    for line in sub:
        text(MARGIN, y, line, 26, "Archivo")
        y += 26 * 1.4
    foot_h = len(foot) * 26 * 1.35
    y0 = y + 26
    y1 = h - 36 - foot_h - 22
    step = (y1 - y0) / len(rows)
    full = W - 2 * MARGIN
    for i, r in enumerate(rows):
        top = y0 + i * step
        text(MARGIN, top, r["label"], 28 if square else 26, "Archivo", "semibold")
        by = top + (28 if square else 26) * 1.3 + lab_gap
        ax.add_patch(plt.Rectangle((MARGIN, by), r["share"] * full, bar_h, color=RED if r["accent"] else NAVY, lw=0))
        text(MARGIN + 14, by + bar_h / 2, f"${r['usd']:,.0f} · {pct(r['share'])}", 26, "Archivo", "semibold", WHITE, va="center")
    ax.plot([W - MARGIN] * 2, [y0 - 8, y1], color=NAVY, lw=1.5, solid_capstyle="butt")
    ax.plot([MARGIN, W - MARGIN], [h - 36 - foot_h - 10] * 2, color=NAVY, lw=1.5)
    y = h - 36 - foot_h
    for line in foot:
        text(MARGIN, y, line, 26, "Archivo")
        y += 26 * 1.35
    fig.savefig(path, dpi=DPI, facecolor=WHITE)
    plt.close(fig)
    print("wrote", path, "min text px", min(used))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        R = sys.argv[1]
    load_fonts()
    draw(os.path.join(R, "mev-get-back-landscape.png"), 768, False)
    draw(os.path.join(R, "mev-get-back-square.png"), 1024, True)
