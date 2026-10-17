"""Quick probe: scan recent Ethereum blocks for Uniswap v2/v3/v4 swaps and
flag same-block sandwiches with a Dune-spellbook-style rule. Exploratory only."""
import json, sys, time, urllib.request, collections

RPC = "https://rpc.mevblocker.io"
V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V4 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
V4PM = "0x000000000004444c5dc75cb358380d2e3de08a90"
NBLOCKS = int(sys.argv[1]) if len(sys.argv) > 1 else 600
OUT = sys.argv[2]


def rpc(method, params, tries=5):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "probe"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
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


head = int(rpc("eth_blockNumber", []), 16) - 5
start = head - NBLOCKS + 1
swaps = []
for a in range(start, head + 1, 100):
    b = min(a + 99, head)
    logs = rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(b), "topics": [[V2, V3, V4]]}])
    for lg in logs:
        t0 = lg["topics"][0]
        data = lg["data"][2:]
        w = [data[i:i + 64] for i in range(0, len(data), 64)]
        if t0 == V2:
            a0in, a1in, a0out, a1out = (int(x, 16) for x in w[:4])
            pool, z4o = lg["address"].lower(), a0in > 0
            amt_in, amt_out = (a0in, a1out) if z4o else (a1in, a0out)
            ver = "v2"
        elif t0 == V3:
            a0, a1 = s256(w[0]), s256(w[1])
            pool, z4o = lg["address"].lower(), a0 > 0
            amt_in, amt_out = (a0, -a1) if z4o else (a1, -a0)
            ver = "v3"
        else:
            if lg["address"].lower() != V4PM:
                continue
            a0, a1 = s256(w[0]), s256(w[1])  # caller deltas: negative = paid in
            pool, z4o = "v4:" + lg["topics"][1], a0 < 0
            amt_in, amt_out = (-a0, a1) if z4o else (-a1, a0)
            ver = "v4"
        swaps.append(dict(block=int(lg["blockNumber"], 16), tx=lg["transactionHash"],
                          txi=int(lg["transactionIndex"], 16), li=int(lg["logIndex"], 16),
                          pool=pool, ver=ver, z4o=z4o, amt_in=amt_in, amt_out=amt_out))
print(f"blocks {start}-{head}: {len(swaps)} swaps", file=sys.stderr)

# tx_from for every tx that swapped
need = sorted({s["block"] for s in swaps})
frm = {}
for bn in need:
    blk = rpc("eth_getBlockByNumber", [hex(bn), True])
    for tx in blk["transactions"]:
        frm[tx["hash"]] = tx["from"].lower()
for s in swaps:
    s["from"] = frm.get(s["tx"])

by = collections.defaultdict(list)
for s in swaps:
    by[(s["block"], s["pool"])].append(s)

sandwiches = []
for (bn, pool), ss in by.items():
    ss.sort(key=lambda s: s["li"])
    for i, f in enumerate(ss):
        for j in range(i + 2, len(ss)):
            bk = ss[j]
            if bk["from"] != f["from"] or bk["tx"] == f["tx"] or bk["z4o"] == f["z4o"]:
                continue
            victims = [v for v in ss[i + 1:j] if v["z4o"] == f["z4o"] and v["from"] != f["from"]]
            if not victims:
                continue
            ratio = bk["amt_in"] / f["amt_out"] if f["amt_out"] else None
            sandwiches.append(dict(block=bn, pool=pool, ver=f["ver"], attacker=f["from"],
                                   front=f["tx"], back=bk["tx"], victims=[v["tx"] for v in victims],
                                   amount_ratio=ratio, gross_profit_raw=bk["amt_out"] - f["amt_in"]))
            break

pool_swaps = collections.Counter(s["pool"] for s in swaps)
pool_ver = {s["pool"]: s["ver"] for s in swaps}
pool_sw = collections.Counter(x["pool"] for x in sandwiches)
pool_vic = collections.Counter()
for x in sandwiches:
    pool_vic[x["pool"]] += len(x["victims"])
strict = [x for x in sandwiches if x["amount_ratio"] and 0.9 <= x["amount_ratio"] <= 1.1]
json.dump(dict(start=start, head=head, n_swaps=len(swaps), sandwiches=sandwiches,
               pool_swaps=pool_swaps, pool_ver=pool_ver), open(OUT, "w"))
print(f"swaps={len(swaps)} pools={len(pool_swaps)} sandwiches(loose)={len(sandwiches)} "
      f"sandwiches(Qin 90-110%)={len(strict)} victims={sum(pool_vic.values())}")
print("by version (swaps / sandwiches):", {v: (sum(1 for s in swaps if s['ver'] == v), sum(1 for x in sandwiches if x['ver'] == v)) for v in ('v2', 'v3', 'v4')})
print("attackers:", collections.Counter(x["attacker"] for x in strict).most_common(5))
print("top sandwiched pools: pool ver sandwiches victims swaps_in_pool")
for p, n in pool_sw.most_common(15):
    print(p, pool_ver[p], n, pool_vic[p], pool_swaps[p])
for p in ["0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
          "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc", "0x11b815efb8f581194ae79006d24e0d814b7697f6",
          "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36", "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"]:
    print("ref", p, pool_ver.get(p), "swaps", pool_swaps.get(p, 0), "sandwiches", pool_sw.get(p, 0), "victims", pool_vic.get(p, 0))
