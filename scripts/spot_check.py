"""Draw a blind spot-check sample from the multi-pool detections.

usage: python scripts/spot_check.py results/multi-pool/sandwiches.csv results/spot-check [N] [SEED]

Writes
  OUT/sample.md       what a reviewer sees: pool, block, the three kinds of transaction and Etherscan links.
                      It carries no detector output (no ratio, strict flag, attacker address, label).
  OUT/labels.csv      a blank sheet to fill in: one row per candidate, empty `your_label` and `notes`.
  OUT/answer-key.csv  the detector's output for the same candidates. Open it only after labelling.
The draw is uniform over all detections (random.Random(SEED)); it is not stratified by pool or week.
"""
import csv
import os
import random
import sys

N_DEFAULT, SEED_DEFAULT = 10, 20261025
TX = "https://etherscan.io/tx/"
BLOCK = "https://etherscan.io/block/"


def main():
    src, out = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else N_DEFAULT
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else SEED_DEFAULT
    rows = list(csv.DictReader(open(src)))
    pick = random.Random(seed).sample(rows, n)
    os.makedirs(out, exist_ok=True)
    pools = {"usdc-weth-0.01": "USDC/WETH 0.01%", "weth-usdt-0.01": "WETH/USDT 0.01%", "usdc-weth-0.05": "USDC/WETH 0.05%"}
    md = ["# Sandwich spot-check sample", "",
          f"{n} candidates drawn at random (seed {seed}) from {len(rows)} detections. Labels are hidden: "
          "this file shows only what is on chain.", "",
          "For each candidate, open the three links on Etherscan and decide:", "",
          "- **S**: a sandwich. One address trades first in the block, a different user's swap on the same pool follows "
          "in the same direction, and the first address trades back the other way afterwards.",
          "- **N**: not a sandwich (for example an arbitrage or a rebalance, or the middle swap is not a different "
          "user trading the same way).",
          "- **U**: unsure.", "",
          "On each transaction page, check the block position (`Position in block`) and the swap rows. "
          "Record the labels in `labels.csv`. Do not open `answer-key.csv` until you finish.", ""]
    labels = [["id", "your_label", "notes"]]
    key = []
    for i, r in enumerate(pick, 1):
        victims = r["victims"].split()
        md += [f"## Candidate {i}", "",
               f"- Pool: {pools.get(r['pool_key'], r['pool_key'])}",
               f"- Block: [{r['block']}]({BLOCK}{r['block']})",
               f"- Possible front-run: [{r['front']}]({TX}{r['front']})"]
        md += [f"- Possible victim {k}: [{v}]({TX}{v})" for k, v in enumerate(victims, 1)]
        md += [f"- Possible back-run: [{r['back']}]({TX}{r['back']})", ""]
        labels.append([i, "", ""])
        key.append(dict(id=i, pool_key=r["pool_key"], week_start=r["week_start"], block=r["block"],
                        attacker_eoa=r["attacker_eoa"], attacker_to=r["attacker_to"], ratio=r["ratio"],
                        strict=r["strict"], n_victims=len(victims), detector_label="sandwich"))
    open(os.path.join(out, "sample.md"), "w").write("\n".join(md))
    csv.writer(open(os.path.join(out, "labels.csv"), "w", newline="")).writerows(labels)
    with open(os.path.join(out, "answer-key.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(key[0]))
        w.writeheader()
        w.writerows(key)


if __name__ == "__main__":
    main()
