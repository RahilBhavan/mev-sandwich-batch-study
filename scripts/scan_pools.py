"""Pool selection scan: count same-block sandwiches on a fixed list of candidate
Uniswap v2/v3 pools over a block range. Exploratory; detection rule is in
docs/research.md (Dune-style ordering + Qin et al. amount match).

usage: [POOLS=addr,addr] python scan_pools.py NBLOCKS OUT.json [END_BLOCK]
"""
import collections
import json
import os
import sys
import time
import urllib.request

RPC = os.environ.get("RPC", "https://rpc.mevblocker.io")
V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
POOLS = {
    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640": "v3 USDC/WETH 0.05%",
    "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8": "v3 USDC/WETH 0.30%",
    "0x11b815efb8f581194ae79006d24e0d814b7697f6": "v3 WETH/USDT 0.05%",
    "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36": "v3 WETH/USDT 0.30%",
    "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b": "v3 WETH/USDT 0.01%",
    "0x11950d141ecb863f01007add7d1a342041227b58": "v3 PEPE/WETH 0.30%",
    "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc": "v2 USDC/WETH",
    "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852": "v2 WETH/USDT",
    "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f": "v2 PEPE/WETH",
}
if os.environ.get("POOLS"):  # comma-separated subset, e.g. POOLS=0x88e6...
    POOLS = {p: POOLS[p] for p in os.environ["POOLS"].lower().split(",")}
CHUNK = int(os.environ.get("CHUNK", "1000"))


def rpc(method, params, tries=6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "scan"})
            d = json.load(urllib.request.urlopen(req, timeout=90))
            if "result" in d:
                return d["result"]
            print("err", d.get("error"), file=sys.stderr)
        except Exception as e:
            print("exc", e, file=sys.stderr)
        time.sleep(2 * (i + 1))
    raise RuntimeError(method)


def s256(h):
    v = int(h, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def parse(lg):
    w = [lg["data"][2 + i:2 + i + 64] for i in range(0, len(lg["data"]) - 2, 64)]
    if lg["topics"][0] == V2:
        a0in, a1in, a0out, a1out = (int(x, 16) for x in w[:4])
        z4o = a0in > 0
        amt_in, amt_out = (a0in, a1out) if z4o else (a1in, a0out)
    else:
        a0, a1 = s256(w[0]), s256(w[1])
        z4o = a0 > 0
        amt_in, amt_out = (a0, -a1) if z4o else (a1, -a0)
    return dict(block=int(lg["blockNumber"], 16), tx=lg["transactionHash"], li=int(lg["logIndex"], 16),
                pool=lg["address"].lower(), z4o=z4o, amt_in=amt_in, amt_out=amt_out)


def candidates(ss):
    """(front, back, victims) triples by ordering/direction only; attacker identity checked later."""
    out = []
    for i, f in enumerate(ss):
        for j in range(i + 2, len(ss)):
            bk = ss[j]
            if bk["z4o"] == f["z4o"] or bk["tx"] == f["tx"]:
                continue
            vic = [v for v in ss[i + 1:j] if v["z4o"] == f["z4o"] and v["tx"] not in (f["tx"], bk["tx"])]
            if vic:
                out.append((f, bk, vic))
    return out


def main():
    nblocks, out = int(sys.argv[1]), sys.argv[2]
    end = int(sys.argv[3]) if len(sys.argv) > 3 else int(rpc("eth_blockNumber", []), 16) - 10
    start = end - nblocks + 1
    swaps = []
    for a in range(start, end + 1, CHUNK):
        b = min(a + CHUNK - 1, end)
        logs = rpc("eth_getLogs", [{"address": list(POOLS), "fromBlock": hex(a), "toBlock": hex(b),
                                    "topics": [[V2, V3]]}])
        swaps += [parse(lg) for lg in logs]
        print(f"{b - start + 1}/{nblocks} blocks, {len(swaps)} swaps", file=sys.stderr)

    by = collections.defaultdict(list)
    for s in swaps:
        by[(s["block"], s["pool"])].append(s)
    cand = {k: candidates(sorted(v, key=lambda s: s["li"])) for k, v in by.items()}
    cand = {k: v for k, v in cand.items() if v}

    # tx sender (EOA) and target (bot contract) only for blocks with ordering candidates
    meta = {}
    for bn in sorted({k[0] for k in cand}):
        for tx in rpc("eth_getBlockByNumber", [hex(bn), True])["transactions"]:
            meta[tx["hash"]] = (tx["from"].lower(), (tx["to"] or "").lower())

    sandwiches = []
    for (bn, pool), triples in cand.items():
        used = set()
        for f, bk, vic in triples:
            if f["tx"] in used:
                continue
            ff, ft = meta[f["tx"]]
            bf, bt = meta[bk["tx"]]
            same_eoa, same_bot = ff == bf, ft == bt
            ratio = bk["amt_in"] / f["amt_out"] if f["amt_out"] else 0
            # same EOA, or same target contract with a tight amount match (filters shared routers)
            if not (same_eoa or (same_bot and 0.99 <= ratio <= 1.01)):
                continue
            victims = [v["tx"] for v in vic if meta[v["tx"]][0] not in (ff, bf)]
            if not victims:
                continue
            used.add(f["tx"])
            sandwiches.append(dict(block=bn, pool=pool, attacker_eoa=ff, attacker_to=ft, front=f["tx"],
                                   back=bk["tx"], victims=victims, amount_ratio=ratio,
                                   qin_match=0.9 <= ratio <= 1.1,
                                   gross_profit_raw=bk["amt_out"] - f["amt_in"]))

    swaps_n = collections.Counter(s["pool"] for s in swaps)
    sw_n = collections.Counter(x["pool"] for x in sandwiches if x["qin_match"])
    vic_n = collections.Counter()
    for x in sandwiches:
        if x["qin_match"]:
            vic_n[x["pool"]] += len(x["victims"])
    json.dump(dict(start=start, end=end, rpc=RPC, pools=POOLS, n_swaps=len(swaps),
                   sandwiches=sandwiches), open(out, "w"), indent=1)
    print(f"blocks {start}-{end} ({nblocks})")
    print(f"{'pool':<22}{'swaps':>8}{'sandwiches':>12}{'victims':>9}")
    for p, name in POOLS.items():
        print(f"{name:<22}{swaps_n[p]:>8}{sw_n[p]:>12}{vic_n[p]:>9}")
    print("loose-only (amount outside 90-110%):", sum(1 for x in sandwiches if not x["qin_match"]))


if __name__ == "__main__":
    main()
