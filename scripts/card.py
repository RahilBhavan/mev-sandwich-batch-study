"""The two post cards: how much of the week's sandwich loss victims get back, and how much slippage attackers took.

usage: python scripts/card.py [RESULTS]
reads RESULTS/victims.csv and RESULTS/summary.json and writes, at exactly 1024x640 and 1024x1024 px:
  RESULTS/mev-get-back-{landscape,square}.png and RESULTS/slippage-taken-{landscape,square}.png,
  RESULTS/card-alt-text.md (built from the same rows as the bars) and RESULTS/cards.sha256 (PNG hashes).
The design rules are in DESIGN.md. Every size below is px on the 1024px-wide canvas; the smallest text is MIN_TEXT_PX.
"""
import csv
import hashlib
import json
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
MIN_TEXT_PX = 26
W, MARGIN, DPI = 1024, 48, 100
SIZES = {"landscape": 640, "square": 1024}

MEV_SUBTITLE = "No sandwich made money under batch clearing."
MEV_AXIS = "Share of the $12,387 loss victims get back"
SLIP_AXIS = "Dollars of slippage tolerance, 115 victims"
ATTACKER_LABEL = "Attacker, no slippage limit (arrival)"
EVERY_ORDER_LABEL = "Every order, no slippage limits (arrival)"
RANDOM_LABEL = "Same orders, random tie-break (mean of 200)"
STAY_OUT_LABEL = "If attackers stay out: about 100%"

# (label, victims.csv column, summary.json share key, highlighted). Shares equal results/summary.json prevented_share_*.
SCENARIOS = [
    ("Same orders, arrival order", "mech_gain_usd", "prevented_share_static_arrival", False),
    (RANDOM_LABEL, "mech_gain_mean", "prevented_share_static_random_mean", True),
    (ATTACKER_LABEL, "mech_gain_attacker_unlimited_usd", "prevented_share_static_attacker_unlimited_arrival", False),
    (EVERY_ORDER_LABEL, "mech_gain_unlimited_usd", "prevented_share_static_all_unlimited", False),
    (STAY_OUT_LABEL, "mech_gain_attacker_removed_usd", "prevented_share_deterred", False),
]


def num(x):
    return float(x) if x not in ("", None) else 0.0


def victims(results):
    return [y for y in csv.DictReader(open(os.path.join(results, "victims.csv"))) if num(y["loss_a_usd"]) > 0]


def scenarios(results="results"):
    """Total victim loss and, per scenario, the dollars returned (each victim capped at its own loss)."""
    vic = victims(results)
    loss = sum(num(y["loss_a_usd"]) for y in vic)
    rows = []
    for label, col, _, accent in SCENARIOS:
        got = sum(min(max(num(y[col]), 0), num(y["loss_a_usd"])) for y in vic)
        rows.append(dict(label=label, usd=got, share=got / loss, accent=accent))
    return loss, rows


def slippage(results="results"):
    """The victims whose calldata decodes with a non-zero minimum: how many, their tolerance and what attackers took."""
    c = [y for y in victims(results) if y["slippage_slack_c_usd"] != ""]
    return len(c), sum(num(y["slippage_slack_c_usd"]) for y in c), sum(num(y["loss_a_usd"]) for y in c)


def mev_card(results, square):
    loss, rows = scenarios(results)
    s = json.load(open(os.path.join(results, "summary.json")))
    p5, p95 = round(s["prevented_share_static_random_p5"] * 100), round(s["prevented_share_static_random_p95"] * 100)
    out = []
    for r in rows:
        pct = f"{r['share']:.0%}"
        if r["label"] == STAY_OUT_LABEL:
            out.append(dict(label=STAY_OUT_LABEL, bar=f"≈ ${r['usd']:,.0f}", frac=r["share"], accent=False, alt=STAY_OUT_LABEL))
            continue
        rng = f"p5-p95 {p5}-{p95}%"
        label = r["label"] + (f": {rng}" if r["accent"] else "")
        out.append(dict(label=label, bar=f"${r['usd']:,.0f} · {pct}", frac=r["share"], accent=r["accent"],
                        alt=f"{r['label']}: {pct}" + (f" ({rng})" if r["accent"] else "")))
    lead = round(rows[1]["share"] * 100)
    k = f"${loss / 1000:.1f}k"
    title = [f"Per-block clearing hands victims", f"back about {lead}% of a week’s", f"{k} sandwich loss"] if square else \
        ["Per-block clearing hands victims back", f"about {lead}% of a week’s {k} sandwich loss"]
    sub = [MEV_SUBTITLE]
    foot = ["Uniswap v3 WETH/USDT 0.01%, 5–11 Oct 2026, 236 sandwiches.",
            f"Source: rpc.mevblocker.io logs; Chan, Wu & Shi, AFT 2025. As of {AS_OF}."]
    return dict(title=title, sub=sub, rows=out, axis=MEV_AXIS, ticks=("0%", "100%"), foot=foot,
                alt_title=" ".join(title), alt_sub=MEV_SUBTITLE)


def slippage_card(results, square):
    n, tolerance, taken = slippage(results)
    share = f"{taken / tolerance:.0%}"
    rows = [dict(label=f"Tolerance the {n} victims set", bar=f"${tolerance:,.0f} · 100%", frac=1.0, accent=False,
                 alt=f"Tolerance the {n} victims set: ${tolerance:,.0f}"),
            dict(label="Taken by the attackers", bar=f"${taken:,.0f} · {share}", frac=taken / tolerance, accent=True,
                 alt=f"Taken by the attackers: ${taken:,.0f}, {share}")]
    title = ["Attackers took 98% of the", "slippage victims allowed"] if square else \
        ["Attackers took 98% of the slippage", "victims allowed"]
    assert share == "98%"
    sub = [f"{n} of 244 victims set a decodable, non-zero minimum;", "29 more set none and are left out."]
    foot = ["Uniswap v3 WETH/USDT 0.01%, 5–11 Oct 2026.",
            f"Source: rpc.mevblocker.io logs, router calldata. As of {AS_OF}."]
    return dict(title=title, sub=sub, rows=rows, axis=SLIP_AXIS, ticks=("$0", f"${tolerance:,.0f}"), foot=foot,
                alt_title=" ".join(title), alt_sub=" ".join(sub))


CARDS = {"mev-get-back": mev_card, "slippage-taken": slippage_card}


def load_fonts():
    for f in ("RobotoSlab-Bold.ttf", "Archivo-Regular.ttf", "Archivo-SemiBold.ttf"):
        font_manager.fontManager.addfont(os.path.join(HERE, "card-fonts", f))


def draw(path, h, square, spec):
    tpx = 48 if square else 34
    lab_px, bar_h, lab_gap = (28, 52, 6) if square else (26, 30, 2)
    fig = plt.figure(figsize=(W / DPI, h / DPI), dpi=DPI)
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
        t = ax.text(x, y, s, fontsize=px * 72 / DPI, family=family, weight=weight, color=color, ha=ha, va=va)
        bb = t.get_window_extent(rend)
        assert bb.x0 >= MARGIN - 1 and bb.x1 <= W - MARGIN + 1, (s, bb.x0, bb.x1)
        used.append(px)

    y = 24 if not square else 44
    for line in spec["title"]:
        text(MARGIN, y, line, tpx, "Roboto Slab", "bold")
        y += tpx * (1.2 if square else 1.15)
    y += 8 if not square else 16
    for line in spec["sub"]:
        text(MARGIN, y, line, 26, "Archivo")
        y += 26 * 1.25
    foot_line = 26 * 1.25
    foot_top = h - 18 - len(spec["foot"]) * foot_line
    axis_top = foot_top - 14 - 26 * 1.3
    rows_top = y + (10 if not square else 28)
    rows_bot = axis_top - 8
    n = len(spec["rows"])
    step = (rows_bot - rows_top) / n
    full = W - 2 * MARGIN
    bar_h = max(bar_h, min(96, step - lab_px * 1.15 - lab_gap - 40))  # few rows: taller bars
    assert step >= lab_px * 1.15 + lab_gap + bar_h - 1, ("rows do not fit", step)
    for i, r in enumerate(spec["rows"]):
        top = rows_top + i * step
        text(MARGIN, top, r["label"], lab_px, "Archivo", "semibold")
        by = top + lab_px * 1.15 + lab_gap
        ax.add_patch(plt.Rectangle((MARGIN, by), r["frac"] * full, bar_h, color=RED if r["accent"] else NAVY, lw=0))
        text(MARGIN + 14, by + bar_h / 2, r["bar"], 26, "Archivo", "semibold", WHITE, va="center")
    ax.plot([MARGIN, MARGIN], [rows_top, rows_bot], color=NAVY, lw=1.5, solid_capstyle="butt")
    ax.plot([W - MARGIN] * 2, [rows_top, rows_bot], color=NAVY, lw=1.5, solid_capstyle="butt")
    ax.plot([MARGIN, W - MARGIN], [rows_bot + 2] * 2, color=NAVY, lw=1.5)
    text(MARGIN, axis_top, spec["ticks"][0], 26, "Archivo")
    text(W / 2, axis_top, spec["axis"], 26, "Archivo", "semibold", ha="center")
    text(W - MARGIN, axis_top, spec["ticks"][1], 26, "Archivo", ha="right")
    ax.plot([MARGIN, W - MARGIN], [foot_top - 8] * 2, color=NAVY, lw=1.5)
    y = foot_top
    for line in spec["foot"]:
        text(MARGIN, y, line, 26, "Archivo")
        y += foot_line
    fig.savefig(path, dpi=DPI, facecolor=WHITE)
    plt.close(fig)
    print("wrote", path, f"{W}x{h}", "min text px", min(used))


def alt_text(name, spec):
    """Alt text built from the rows that are drawn, in drawn order."""
    return f"{spec['alt_title']}. {spec['alt_sub']} " + " ".join(f"{r['alt']}." for r in spec["rows"]) + \
        f" Source: Ethereum logs via rpc.mevblocker.io, as of {AS_OF}."


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(results):
    load_fonts()
    alts, hashes = [], []
    for name, build in CARDS.items():
        for shape, h in SIZES.items():
            spec = build(results, shape == "square")
            fname = f"{name}-{shape}.png"
            draw(os.path.join(results, fname), h, shape == "square", spec)
            hashes.append(f"{sha256(os.path.join(results, fname))}  {fname}")
            if shape == "square":
                alts.append(f"## {fname} and {name}-landscape.png\n\n{alt_text(name, build(results, True))}\n")
    open(os.path.join(results, "card-alt-text.md"), "w").write(
        "# Card alt text\n\nWritten by `scripts/card.py` from the rows each card draws; the landscape and square cards "
        "carry the same rows.\n\n" + "\n".join(alts))
    open(os.path.join(results, "cards.sha256"), "w").write("\n".join(hashes) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        R = sys.argv[1]
    main(R)
