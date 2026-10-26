"""Run the study's sandwich detector (mev/detect.py, unchanged) on several pools and weeks.

usage: python scripts/multi_scan.py CACHE_DIR OUT_DIR [POOL ...]      (pools default to all in POOLS)

Per pool and week it pulls the Swap logs over JSON-RPC (1,000-block chunks), keeps only blocks where the
detector could find anything, fetches sender and target for the transactions in those blocks, and calls
`detect.detect` with the same window as `scripts/analyze.py` (`detect.QIN`).

The block filter changes no result. A sandwich needs a front-run leg, a victim leg in the front-run's direction
and a back-run leg in the opposite direction, all in one block, so a block with fewer than three transaction legs,
or without that order of directions, cannot hold one. `keep_block` implements it on the same `detect.legs` the
detector uses; `--no-filter` turns it off, and the check on the original week compares both.

This script measures detection only. It does not replay swaps, so it reports no victim loss.
Raw RPC responses are cached under CACHE_DIR, so a rerun is resumable and makes no new calls.
"""
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import detect, rpc
from mev.pool import T_SWAP, decode

# Pools chosen by rule: the three Uniswap v3 pools with the most swaps on 7 Oct 2026 (blocks 26,136,840-26,144,039),
# from the all-pool scan `scripts/probe_all_pools.py`. v2 and v4 pools are excluded: the detector and the exact
# swap math in this repository are v3-only.
POOLS = {
    "usdc-weth-0.01": ("USDC/WETH 0.01%", "0xe0554a476a092703abdb3ef35c80e0d76d32939f"),
    "weth-usdt-0.01": ("WETH/USDT 0.01%", "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b"),
    "usdc-weth-0.05": ("USDC/WETH 0.05%", "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"),
}
# Monday 00:00:00 to Sunday 23:59:59 UTC, found by binary search on block timestamps (`block_range`).
WEEKS = {
    "2026-09-14": None, "2026-09-21": None, "2026-09-28": None,
    "2026-10-05": (26122440, 26172657),  # the original study week, fixed in mev/pool.py
}
CHUNK = 1000


def cached(path, fn):
    if os.path.exists(path):
        return json.load(open(path))
    v = fn()
    json.dump(v, open(path + ".tmp", "w"))
    os.replace(path + ".tmp", path)
    return v


def week_start_ts(day):
    import calendar
    import time
    return calendar.timegm(time.strptime(day, "%Y-%m-%d"))


def block_range(day, cache):
    """First and last block of the UTC week starting on `day`."""
    def first_at(ts):
        return cached(os.path.join(cache, f"first-block-{ts}.json"),
                      lambda: rpc.block_at_or_after(ts, 20_000_000, int(rpc.call("eth_blockNumber", []), 16)))
    s = week_start_ts(day)
    return first_at(s), first_at(s + 7 * 86400) - 1


def swaps_for(pool, a, b, cache):
    out = []
    for s in range(a, b + 1, CHUNK):
        e = min(s + CHUNK - 1, b)
        logs = cached(os.path.join(cache, f"swaps-{pool[:10]}-{s}-{e}.json"), lambda: rpc.call(
            "eth_getLogs", [{"address": pool, "fromBlock": hex(s), "toBlock": hex(e), "topics": [T_SWAP]}]))
        out += [d for d in (decode(lg) for lg in logs if not lg.get("removed")) if d]
    return out


def keep_block(swaps):
    """True if the block has legs in an order that could hold a sandwich (see module docstring)."""
    L = detect.legs(swaps)
    for i, f in enumerate(L):
        v = next((k for k in range(i + 1, len(L)) if L[k]["z4o"] == f["z4o"]), None)
        if v is not None and any(L[k]["z4o"] != f["z4o"] for k in range(v + 1, len(L))):
            return True
    return False


def tx_meta(hashes, cache, tag):
    hashes = sorted(hashes)
    out = {}
    B = 500
    for k in range(0, len(hashes), B):
        part = hashes[k:k + B]
        res = cached(os.path.join(cache, f"txs-{tag}-{k:06d}.json"), lambda: [
            None if t is None else {"hash": t["hash"], "from": t["from"], "to": t["to"]}
            for t in rpc.batch([("eth_getTransactionByHash", [h]) for h in part], size=50)])
        for h, t in zip(part, res):
            if t is None:
                raise RuntimeError(f"transaction {h} not returned")
            out[h] = t
    return out


def scan(key, day, cache, use_filter=True):
    name, pool = POOLS[key]
    a, b = WEEKS[day] or block_range(day, cache)
    swaps = swaps_for(pool, a, b, cache)
    by = collections.defaultdict(list)
    for s in swaps:
        by[s["block"]].append(s)
    kept = {bn: ss for bn, ss in by.items() if not use_filter or keep_block(ss)}
    flat = [s for ss in kept.values() for s in ss]
    txs = tx_meta({s["tx"] for s in flat}, cache, f"{pool[:10]}-{a}") if flat else {}
    sws = detect.detect(flat, txs, detect.QIN)
    strict = [s for s in sws if s["strict"]]
    attackers = collections.Counter(s["attacker_eoa"] for s in sws)
    return dict(pool_key=key, pool=name, address=pool, week_start=day, blocks=[a, b],
                swaps=len(swaps), swap_txs=len({s["tx"] for s in swaps}), blocks_checked=len(kept),
                txs_fetched=len(txs), sandwiches=len(sws), sandwiches_strict=len(strict),
                victims=sum(len(s["victims"]) for s in sws),
                attackers=len(attackers), top_attacker_share=round(max(attackers.values()) / len(sws), 3) if sws else None,
                top_attacker=attackers.most_common(1)[0][0] if sws else None), sws


def table(rows):
    """Markdown table of one row per pool and week, plus a total per pool."""
    lines = ["| Pool | Week (UTC, Monday) | Swaps | Sandwiches | Strict ±1% | Victims | Attacker addresses | Top attacker share |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for key in dict.fromkeys(r["pool_key"] for r in rows):
        rs = [r for r in rows if r["pool_key"] == key]
        for r in rs:
            share = f"{r['top_attacker_share']:.0%}" if r["top_attacker_share"] is not None else "n/a"
            lines.append(f"| {r['pool']} | {r['week_start']} | {r['swaps']:,} | {r['sandwiches']} | "
                         f"{r['sandwiches_strict']} | {r['victims']} | {r['attackers']} | {share} |")
        lines.append(f"| **{rs[0]['pool']} total** | 4 weeks | **{sum(r['swaps'] for r in rs):,}** | "
                     f"**{sum(r['sandwiches'] for r in rs)}** | **{sum(r['sandwiches_strict'] for r in rs)}** | "
                     f"**{sum(r['victims'] for r in rs)}** | | |")
    return "\n".join(lines) + "\n"


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    cache, out = args[0], args[1]
    if "--table-only" in sys.argv:  # rebuild table.md from an existing summary.json, no RPC
        open(os.path.join(out, "table.md"), "w").write(table(json.load(open(os.path.join(out, "summary.json")))))
        return
    keys = args[2:] or list(POOLS)
    use_filter = "--no-filter" not in sys.argv
    os.makedirs(cache, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    rows, hits = [], []
    for key in keys:
        for day in WEEKS:
            r, sws = scan(key, day, cache, use_filter)
            print(json.dumps(r), flush=True)
            rows.append(r)
            for s in sws:
                hits.append(dict(pool_key=key, week_start=day, block=s["block"], front=s["front"], back=s["back"],
                                 victims=" ".join(s["victims"]), attacker_eoa=s["attacker_eoa"],
                                 attacker_to=s["attacker_to"], ratio=round(s["ratio"], 4), strict=s["strict"]))
    json.dump(rows, open(os.path.join(out, "summary.json"), "w"), indent=1)
    open(os.path.join(out, "table.md"), "w").write(table(rows))
    with open(os.path.join(out, "sandwiches.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hits[0]))
        w.writeheader()
        w.writerows(hits)


if __name__ == "__main__":
    main()
