"""Compare this study's detections with a Dune export of docs/dune/sandwiches.sql.

usage: python scripts/compare_dune.py DUNE_EXPORT.csv [RESULTS]
Prints agreement on sandwich blocks, attacker legs and victims, and lists disagreements to inspect by hand.
"""
import csv
import os
import sys

dune = list(csv.DictReader(open(sys.argv[1])))
R = sys.argv[2] if len(sys.argv) > 2 else "results"
sw = list(csv.DictReader(open(os.path.join(R, "sandwiches.csv"))))
vic = list(csv.DictReader(open(os.path.join(R, "victims.csv"))))

ours_legs = {h.lower() for x in sw for h in (x["front"], x["back"])}
ours_vic = {y["victim_tx"].lower() for y in vic}
d_legs = {r["tx_hash"].lower() for r in dune if r["role"] == "leg"}
d_vic = {r["tx_hash"].lower() for r in dune if r["role"] == "victim"}
ours_blocks = {x["block"] for x in sw}
d_blocks = {r["block_number"] for r in dune}


def report(name, a, b):
    both = len(a & b)
    print(f"{name}: ours {len(a)}, Dune {len(b)}, both {both}, "
          f"recall vs Dune {both / len(b):.1%}, Dune confirms {both / len(a):.1%}" if a and b else f"{name}: empty")


report("blocks", ours_blocks, d_blocks)
report("attacker legs", ours_legs, d_legs)
report("victims", ours_vic, d_vic)
print("victims only we found:", sorted(ours_vic - d_vic)[:20])
print("victims only Dune found:", sorted(d_vic - ours_vic)[:20])
