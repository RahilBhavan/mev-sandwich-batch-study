"""Re-implement Dune spellbook's sandwich rule (dex_sandwiches.sql / dex_sandwiched.sql, main branch,
read 2026-10-18) on the ingested week, and write its output in the same CSV shape as docs/dune/sandwiches.sql
so scripts/compare_dune.py can compare it with this study's detector.

This replicates Dune's published logic; it is not a query run on Dune's servers.

Rule, per pool and block, one row per swap event (dex.trades granularity):
  legs:    front and back with the same tx_from, different tx, opposite token directions,
           front.evt_index + 1 < back.evt_index, and at least one trade between them in the front-run's
           direction from a different tx_from. No amount check. No whitelist applied.
  victims: every trade strictly between front and back in the front-run's direction (dex_sandwiched).

usage: python scripts/dune_rule.py [DATADIR] [OUT.csv]
"""
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import data

D = sys.argv[1] if len(sys.argv) > 1 else "data/week"
OUT = sys.argv[2] if len(sys.argv) > 2 else "results/dune-rule-replication.csv"


def main():
    events, txs, _ = data.load(D)
    by = collections.defaultdict(list)
    for e in events:
        if e["kind"] == "swap" and (e["amount0"] or e["amount1"]):
            by[e["block"]].append(e)
    frm = {h: t["from"].lower() for h, t in txs.items()}
    legs, victims = {}, {}
    for b, ss in by.items():
        ss.sort(key=lambda s: s["log_index"])
        for f in ss:
            fz = f["amount0"] > 0
            for bk in ss:
                if not (frm[bk["tx"]] == frm[f["tx"]] and bk["tx"] != f["tx"] and (bk["amount0"] > 0) != fz
                        and f["log_index"] + 1 < bk["log_index"]):
                    continue
                between = [v for v in ss if f["log_index"] <= v["log_index"] <= bk["log_index"]
                           and (v["amount0"] > 0) == fz]
                if not any(frm[v["tx"]] != frm[f["tx"]] for v in between):
                    continue
                legs[f["tx"]] = b
                legs[bk["tx"]] = b
                for v in ss:
                    if f["log_index"] < v["log_index"] < bk["log_index"] and (v["amount0"] > 0) == fz:
                        victims[v["tx"]] = b
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["role", "block_number", "tx_hash", "tx_from", "tx_to"])
        for h, b in sorted(legs.items(), key=lambda kv: kv[1]):
            w.writerow(["leg", b, h, frm[h], (txs[h]["to"] or "").lower()])
        for h, b in sorted(victims.items(), key=lambda kv: kv[1]):
            w.writerow(["victim", b, h, frm[h], (txs[h]["to"] or "").lower()])
    print(f"Dune-rule replication: {len(legs)} leg txs in {len(set(legs.values()))} blocks, {len(victims)} victim txs -> {OUT}")


if __name__ == "__main__":
    main()
