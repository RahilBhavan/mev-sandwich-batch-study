"""Evidence sheet for checking detected sandwiches by hand (plan day 5).

For each sandwich (or a seeded random sample of N): how many distinct senders use the front-run's target contract
and each victim's target contract over the week (a public router has many; a bot contract has few), which pools
each leg touched (from full receipts), whether the legs exactly reverse, and the attacker's ENS reverse name.

usage: python scripts/inspect_hits.py [DATADIR] [RESULTS] [N]
writes RESULTS/precision-evidence.csv
"""
import collections
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import data, rpc
from mev.pool import T_SWAP

D = sys.argv[1] if len(sys.argv) > 1 else "data/week"
R = sys.argv[2] if len(sys.argv) > 2 else "results"
N = int(sys.argv[3]) if len(sys.argv) > 3 else 0
V2_SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
V4_SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
ENS_REGISTRY = "0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e"


def keccak(b):
    # tiny pure-python keccak-256 for ENS namehash (no external dependency)
    RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
          0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
          0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
          0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
          0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
    M = (1 << 64) - 1
    rate = 136
    p = bytearray(b) + b"\x01" + b"\x00" * ((rate - (len(b) + 1) % rate) % rate)
    p[-1] |= 0x80
    s = [[0] * 5 for _ in range(5)]
    for off in range(0, len(p), rate):
        for i in range(rate // 8):
            s[i % 5][i // 5] ^= int.from_bytes(p[off + 8 * i:off + 8 * i + 8], "little")
        for rnd in range(24):
            c = [s[x][0] ^ s[x][1] ^ s[x][2] ^ s[x][3] ^ s[x][4] for x in range(5)]
            d = [c[(x - 1) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & M) for x in range(5)]
            s = [[s[x][y] ^ d[x] for y in range(5)] for x in range(5)]
            bb = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = ROT[x][y]
                    bb[y][(2 * x + 3 * y) % 5] = ((s[x][y] << r) | (s[x][y] >> (64 - r))) & M if r else s[x][y]
            s = [[bb[x][y] ^ ((~bb[(x + 1) % 5][y]) & bb[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
            s[0][0] ^= RC[rnd]
    return b"".join(s[i % 5][i // 5].to_bytes(8, "little") for i in range(4))


def namehash(name):
    node = b"\x00" * 32
    for label in reversed(name.split(".")):
        node = keccak(node + keccak(label.encode()))
    return node


def ens_reverse(addr):
    try:
        node = namehash(addr[2:].lower() + ".addr.reverse")
        res = rpc.call("eth_call", [{"to": ENS_REGISTRY, "data": "0x0178b8bf" + node.hex()}, "latest"])  # resolver(node)
        resolver = "0x" + res[-40:]
        if int(resolver, 16) == 0:
            return ""
        out = bytes.fromhex(rpc.call("eth_call", [{"to": resolver, "data": "0x691f3431" + node.hex()}, "latest"])[2:])
        n = int.from_bytes(out[32:64], "big")
        return out[64:64 + n].decode("utf8", "replace")
    except Exception:
        return ""


def main():
    events, txs, _ = data.load(D)
    sw = list(csv.DictReader(open(os.path.join(R, "sandwiches.csv"))))
    vic = list(csv.DictReader(open(os.path.join(R, "victims.csv"))))
    senders = collections.defaultdict(set)
    for t in txs.values():
        senders[(t["to"] or "").lower()].add(t["from"].lower())
    pick = sw if not N or N >= len(sw) else random.Random(7).sample(sw, N)
    hashes = sorted({h for x in pick for h in (x["front"], x["back"])} |
                    {v["victim_tx"] for v in vic if v["front"] in {x["front"] for x in pick}})
    cache = os.path.join(D, "inspect_receipts.json")
    rc = json.load(open(cache)) if os.path.exists(cache) else {}
    need = [h for h in hashes if h not in rc]
    if need:
        rc.update(zip(need, rpc.batch([("eth_getTransactionReceipt", [h]) for h in need], size=20)))
        json.dump(rc, open(cache, "w"))

    def pools(h):
        out = []
        for lg in rc[h]["logs"]:
            if lg["topics"] and lg["topics"][0] in (T_SWAP, V2_SWAP, V4_SWAP):
                out.append(lg["address"].lower()[:10])
        return "|".join(out)

    names = {}
    rows = []
    for x in pick:
        eoa = x["attacker_eoa"]
        if eoa not in names:
            names[eoa] = ens_reverse(eoa)
        vs = [v for v in vic if v["front"] == x["front"]]
        rows.append(dict(
            block=x["block"], front=x["front"], back=x["back"], attacker_eoa=eoa, attacker_ens=names[eoa],
            attacker_to=x["attacker_to"], attacker_to_senders=len(senders[x["attacker_to"]]),
            same_eoa=txs[x["front"]]["from"].lower() == txs[x["back"]]["from"].lower(),
            ratio=x["ratio"], front_pools=pools(x["front"]), back_pools=pools(x["back"]),
            front_status=int(rc[x["front"]]["status"], 16), back_status=int(rc[x["back"]]["status"], 16),
            victims=" ".join(v["victim_tx"][:12] for v in vs),
            victim_to=" ".join(v["to"] for v in vs),
            victim_to_senders=" ".join(str(len(senders[v["to"]])) for v in vs),
            victim_pools=" ".join(pools(v["victim_tx"]) for v in vs),
            loss_a_usd=sum(float(v["loss_a_usd"]) for v in vs), attacker_gross_b_usd=x["attacker_gross_b_usd"]))
    with open(os.path.join(R, "precision-evidence.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows; attacker EOAs: " + ", ".join(f"{k[:10]}={v or '-'}" for k, v in names.items()))


if __name__ == "__main__":
    main()
