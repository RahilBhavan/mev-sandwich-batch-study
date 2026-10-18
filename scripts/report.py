"""Tables and the figure from results/*.csv.

usage: python scripts/report.py [RESULTS]
writes RESULTS/tables.md, RESULTS/figure.svg, RESULTS/figure.png
"""
import csv
import json
import os
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = sys.argv[1] if len(sys.argv) > 1 else "results"


def num(x):
    return float(x) if x not in ("", None) else 0.0


def tier(e):
    """Robustness tiers from the evidence sheet (scripts/inspect_hits.py)."""
    single = all(p == "0xc7bbec68" for p in e["front_pools"].split("|"))
    strict = 0.99 <= float(e["ratio"]) <= 1.01
    return dict(all=True, strict=strict, core=strict and single and e["same_eoa"] == "True")


def main():
    sw = list(csv.DictReader(open(os.path.join(R, "sandwiches.csv"))))
    vic = list(csv.DictReader(open(os.path.join(R, "victims.csv"))))
    ev = {e["front"]: e for e in csv.DictReader(open(os.path.join(R, "precision-evidence.csv")))}
    summ = json.load(open(os.path.join(R, "summary.json")))
    T = {x["front"]: tier(ev[x["front"]]) for x in sw}
    names = [("all", "All detected (back-run 90–110% of front-run)"), ("strict", "Strict amount match (±1%)"),
             ("core", "Strict, single-pool front-run, same EOA")]
    out = []
    w = out.append

    w("## Table 1. Sandwiches and victim losses, Uniswap v3 WETH/USDT 0.01%, 2026-10-05 to 2026-10-11 UTC\n")
    w("| Detection tier | Sandwiches | Victims | Victim volume | Victim loss (a) | Attacker gross (b) | Attacker gas | Median loss per victim |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, label in names:
        s = [x for x in sw if T[x["front"]][k]]
        fr = {x["front"] for x in s}
        v = [y for y in vic if y["front"] in fr]
        w(f"| {label} | {len(s)} | {len(v)} | ${sum(num(y['victim_volume_usd']) for y in v):,.0f} | "
          f"${sum(num(y['loss_a_usd']) for y in v):,.0f} | ${sum(num(x['attacker_gross_b_usd']) for x in s):,.0f} | "
          f"${sum(num(x['attacker_gas_usd']) for x in s):,.0f} | ${statistics.median(num(y['loss_a_usd']) for y in v):,.2f} |")
    w("")
    c = [y for y in vic if y["slippage_slack_c_usd"] != ""]
    la_c = sum(num(y["loss_a_usd"]) for y in c)
    sl_c = sum(num(y["slippage_slack_c_usd"]) for y in c)
    w(f"Loss measure (c), slippage tolerance available to the attacker, is defined for the {len(c)} victims whose router "
      f"calldata decodes with a non-zero bound: their tolerance totalled ${sl_c:,.0f} and the attackers took ${la_c:,.0f} "
      f"of it ({la_c / sl_c:.0%}); the median victim lost {statistics.median(num(y['loss_a_usd']) / num(y['slippage_slack_c_usd']) for y in c if num(y['slippage_slack_c_usd']) > 0):.0%} of their own tolerance. "
      f"{sum(1 for y in vic if y['limit_src'] == 'calldata_none')} decoded victims set no minimum at all.\n")

    w("## Table 2. The same blocks under Chan–Wu–Shi per-block clearing\n")
    w("Share of victim loss (a) recovered, each victim capped at its own loss. Static = the same orders replayed; "
      "deterred = the attacker's orders removed, because under the mechanism they lose money.\n")
    w("| Detection tier | Attacker net under mechanism, max over all runs | Attacker net, median per sandwich | Deterred | Static, arrival order | Static, random tie-break (mean) | Static, attacker legs without limits (random mean) | Static, every order unlimited |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, label in names:
        s = [x for x in sw if T[x["front"]][k]]
        fr = {x["front"] for x in s}
        v = [y for y in vic if y["front"] in fr and num(y["loss_a_usd"]) > 0]
        L = sum(num(y["loss_a_usd"]) for y in v)
        sh = lambda col: sum(min(max(num(y[col]), 0), num(y["loss_a_usd"])) for y in v) / L
        w(f"| {label} | ${max(num(x['mech_attacker_net_max_all_runs']) for x in s):,.2f} | "
          f"${statistics.median(num(x['mech_attacker_net_usd']) for x in s):,.2f} | {sh('mech_gain_attacker_removed_usd'):.1%} | "
          f"{sh('mech_gain_usd'):.1%} | {sh('mech_gain_mean'):.1%} | {sh('mech_gain_attacker_unlimited_mean'):.1%} | "
          f"{sh('mech_gain_unlimited_usd'):.1%} |")
    w("")
    w(f"Across {summ['draws']} random tie-break draws (all detected), the static share's 5th–95th percentile is "
      f"{summ['prevented_share_static_random_p5']:.1%}–{summ['prevented_share_static_random_p95']:.1%}; with the attacker's "
      f"legs unlimited it is {summ['prevented_share_static_attacker_unlimited_random_p5']:.1%}–"
      f"{summ['prevented_share_static_attacker_unlimited_random_p95']:.1%}. Charging the 0.01% pool fee in phase 1 gives "
      f"{summ['prevented_share_static_fee_phase1']:.1%} (arrival order). Smallest victim fill in the static arrival run: "
      f"{summ['victims_min_fill_static_arrival']:.1%}. Phase-1 gains beyond the sandwich loss (deterred case): "
      f"${summ['excess_deterred_usd']:,.2f}.\n")

    w("## Table 3. Who the victims traded through (all detected)\n")
    w("| Victim transaction target | Victims | Loss (a) |")
    w("|---|---:|---:|")
    labels = {"0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap SwapRouter02",
              "0x66a9893cc07d91d95644aedd05d03f95e1dba8af": "Uniswap Universal Router",
              "0x23617e59a5925b2a4bf75d73ff6711cd0b29de85": "Uniswap Universal Router v2.1.2",
              "0x4c82d1fbfe28c977cbb58d8c7ff8fcf9f70a2cca": "Uniswap Universal Router v2.1.1",
              "0x6131b5fae19ea4f9d964eac0408e4408b66337b5": "KyberSwap MetaAggregationRouterV2",
              "0x0000000000001ff3684f28c67538d4d072c22734": "0x AllowanceHolder",
              "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae": "LI.FI Diamond",
              "0x111111125421ca6dc452d289314280a0f8842a65": "1inch Aggregation Router v6"}
    agg = {}
    for y in vic:
        k = labels.get(y["to"], "Other targets (bots, smart wallets, smaller routers)")
        a = agg.setdefault(k, [0, 0.0])
        a[0] += 1
        a[1] += num(y["loss_a_usd"])
    for k, (n, l) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        w(f"| {k} | {n} | ${l:,.0f} |")
    w("\nLabels are the contracts' Etherscan name tags or public deployment lists (Universal Router v2.1.1/v2.1.2 tags read 2026-10-17).\n")
    open(os.path.join(R, "tables.md"), "w").write("\n".join(out))

    # -- figure: cumulative victim loss, sandwiches ranked by loss ------------------------------------
    per = {}
    for y in vic:
        p = per.setdefault(y["front"], [0.0, 0.0])
        la = num(y["loss_a_usd"])
        p[0] += la
        p[1] += la - min(max(num(y["mech_gain_mean"]), 0), la)
    rows = sorted(per.values(), key=lambda p: -p[0])
    xs = list(range(0, len(rows) + 1))
    cum_sq, cum_m = [0.0], [0.0]
    for a, b in rows:
        cum_sq.append(cum_sq[-1] + a)
        cum_m.append(cum_m[-1] + b)
    INK, GRAY, TXT2, ACC = "#222222", "#8a8a8a", "#595959", "#c2410c"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "text.parse_math": False, "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(10, 7), dpi=160)
    ax.step(xs, cum_sq, where="post", color=GRAY, lw=2)
    ax.step(xs, cum_m, where="post", color=ACC, lw=2.6)
    ax.plot([0, len(rows)], [0, 0], color=GRAY, lw=1.6, ls=(0, (4, 3)))
    n = len(rows)
    ax.text(n + 3, cum_sq[-1], f"Status quo  ${cum_sq[-1]:,.0f}", va="center", color=INK, fontsize=13)
    ax.text(n + 3, cum_m[-1], f"Same orders under\nper-block clearing  ${cum_m[-1]:,.0f}", va="center", color=ACC,
            fontsize=13, fontweight="bold")
    ax.text(n + 3, 350, "Attackers stop\n(no attack profits)  ≈ $0", va="center", color=TXT2, fontsize=12)
    ax.set_xlim(0, n)
    ax.set_ylim(0, cum_sq[-1] * 1.04)
    ax.set_xlabel(f"Sandwiches, ranked by victim loss (n = {n})", color=INK)
    ax.set_ylabel("Cumulative victim loss (USD)", color=INK)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:.0f}k" if v else "$0"))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRAY)
    ax.tick_params(colors=INK)
    fig.suptitle(f"Per-block clearing cuts a week's ${cum_sq[-1] / 1000:,.1f}k sandwich loss\n"
                 f"to ${cum_m[-1] / 1000:,.1f}k with the same orders, and no attack makes money",
                 x=0.03, y=0.975, ha="left", va="top", fontsize=17, fontweight="bold", color=INK, linespacing=1.25)
    fig.text(0.03, 0.835, f"Uniswap v3 WETH/USDT 0.01%, 5–11 Oct 2026, {n} sandwiches. Mechanism: Chan, Wu & Shi (AFT 2025),\n"
             "same orders replayed, mean of 200 random tie-breaks.", ha="left", va="top", fontsize=12, color=INK)
    fig.text(0.03, 0.025, "Loss = victim's output with no front-run minus actual output, by exact Uniswap v3 re-execution.\n"
             "Source: Ethereum logs via rpc.mevblocker.io, pulled 17 Oct 2026. Code: scripts/report.py.",
             ha="left", fontsize=10.5, color=TXT2)
    fig.subplots_adjust(left=0.10, right=0.70, top=0.73, bottom=0.2)
    fig.savefig(os.path.join(R, "figure.svg"))
    fig.savefig(os.path.join(R, "figure.png"))
    print("\n".join(out))


if __name__ == "__main__":
    main()
