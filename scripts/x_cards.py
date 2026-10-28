# design-owner: rahil-design because these are Rahil's public X cards (rahil-design 4.0.1 phone-card path)
"""Card specs for the two Wed Oct 28 X cards (wed28-am-mev, wed28-pm-mev-slippage).

usage: python scripts/x_cards.py [RESULTS]
reads RESULTS/summary.json and RESULTS/victims.csv, writes RESULTS/x-cards/<id>/spec.json and alt.txt.
Every figure comes from the results files, none is typed by hand. Rendering is a separate step: the hub's
rahil-design `social_bars.py spec.json OUT` draws card.png (see results/x-cards/README.md).
"""
import csv
import json
import os
import sys

SOURCE_TAIL = "github.com/RahilBhavan/mev-sandwich-batch-study"
WHEN = "WETH/USDT · Oct 5–11, 2026"


def num(x):
    return float(x) if x not in ("", None) else 0.0


def tolerance(results):
    """Victims with a decoded nonzero limit, their summed tolerance, and what attackers took of it, from victims.csv."""
    vic = [y for y in csv.DictReader(open(os.path.join(results, "victims.csv"))) if num(y["slippage_slack_c_usd"]) > 0]
    slack = sum(num(y["slippage_slack_c_usd"]) for y in vic)
    taken = sum(min(num(y["loss_a_usd"]), num(y["slippage_slack_c_usd"])) for y in vic)
    return len(vic), slack, taken


def pct(x):
    return round(100 * x, 2)


def replay_spec(s):
    arrival, mean = pct(s["prevented_share_static_arrival"]), pct(s["prevented_share_static_random_mean"])
    p5, p95 = pct(s["prevented_share_static_random_p5"]), pct(s["prevented_share_static_random_p95"])
    basis, draws = f"${s['loss_a_usd']:,.0f}", s["draws"]
    return {
        "id": "wed28-am-mev",
        "kind": "range",
        "title": "Order matters.",
        "named": "Order",
        "axis": f"Loss recovered, of {basis}",
        "scale": [0, 100],
        "marker": {"at": arrival, "label": "Arrival order", "text": f"{arrival:.0f}%", "highlight": True},
        "band": {"from": p5, "to": p95, "label": f"{draws} random: mean {mean:.0f}%", "text": f"5th–95th: {p5:.0f}–{p95:.0f}%"},
        "source": WHEN,
        "alt": (f"Order matters. Share of the {basis} sandwich loss recovered in a replay of one WETH/USDT pool, "
                f"Oct 5–11, 2026, keeping the same orders, on a 0–100% scale: arrival order {arrival:.0f}%; across {draws} random "
                f"tie-breaks the mean is {mean:.0f}% and the 5th–95th percentile range is {p5:.0f}–{p95:.0f}%. "
                f"Counterfactual replay, not a deployment. Source: {SOURCE_TAIL}."),
        "scale_labels": "end",
    }


def slippage_spec(s, n, slack, taken):
    share, left = taken / slack, slack - taken
    tol, got = f"${slack:,.0f}", f"${taken:,.0f}"
    return {
        "id": "wed28-pm-mev-slippage",
        "kind": "fill",
        "title": f"{100 * share:.0f}% of the tolerance, taken.",
        "named": f"{100 * share:.0f}%",
        "axis": f"Of {tol}, {n} of {s['victims']} victims",
        "share": round(share, 4),
        "taken": {"label": "Taken", "text": got},
        "left": {"label": "Left", "text": f"${left:,.0f}"},
        "source": WHEN,
        "alt": (f"{100 * share:.0f}% of the tolerance, taken. A bar filled to {100 * share:.0f}%: of {tol} slippage tolerance across {n} of "
                f"{s['victims']} victims with decoded nonzero limits, attackers took {got} and ${left:,.0f} was left. "
                f"Summed dollars, one WETH/USDT pool, Oct 5–11, 2026; the ratio is not per victim or for all trades. "
                f"Source: {SOURCE_TAIL}."),
    }


def specs(results="results"):
    s = json.load(open(os.path.join(results, "summary.json")))
    n, slack, taken = tolerance(results)
    return [replay_spec(s), slippage_spec(s, n, slack, taken)]


if __name__ == "__main__":
    results = sys.argv[1] if len(sys.argv) > 1 else "results"
    for spec in specs(results):
        out = os.path.join(results, "x-cards", spec["id"])
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "spec.json"), "w") as f:
            json.dump(spec, f, indent=1, ensure_ascii=False)
            f.write("\n")
        with open(os.path.join(out, "alt.txt"), "w") as f:
            f.write(spec["alt"] + "\n")
        print("wrote", out)
