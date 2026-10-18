"""Ingest one week of the study pool: logs, transactions and starting state.

usage: python scripts/ingest.py [OUTDIR]   (default data/week)
Resumable: raw RPC responses are cached per chunk under OUTDIR/raw/.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pyarrow as pa
import pyarrow.parquet as pq

from mev import rpc
from mev.pool import POOL, WEEK, T_SWAP, T_MINT, T_BURN, decode

ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
OUT = ARGS[0] if ARGS else "data/week"
RAW = os.path.join(OUT, "raw")
CHUNK = 1000


def cached(path, fn):
    if os.path.exists(path):
        return json.load(open(path))
    v = fn()
    tmp = path + ".tmp"
    json.dump(v, open(tmp, "w"))
    os.replace(tmp, path)
    return v


def eth_call(to, data, block):
    return rpc.call("eth_call", [{"to": to, "data": data}, hex(block)])


# starting state at block a-1: slot0, liquidity and every initialized tick in the week's price range +/- margin
def init_state(swaps, a):
    pre = a - 1
    s0 = eth_call(POOL, "0x3850c7bd", pre)            # slot0()
    L = int(eth_call(POOL, "0x1a686502", pre), 16)    # liquidity()
    sqrtp, tick = int(s0[2:66], 16), int(s0[66:130], 16)
    tick = tick - (1 << 256) if tick >= 1 << 255 else tick
    ticks_seen = [tick] + [d["tick"] for d in swaps]
    lo, hi = min(ticks_seen) - 2000, max(ticks_seen) + 2000
    wlo, whi = lo >> 8, hi >> 8                      # tickSpacing 1: word = tick >> 8
    enc = lambda v: format(v & ((1 << 256) - 1), "064x")
    bm = rpc.batch([("eth_call", [{"to": POOL, "data": "0x5339c296" + enc(w)}, hex(pre)])
                    for w in range(wlo, whi + 1)])   # tickBitmap(int16)
    init = []
    for w, word in zip(range(wlo, whi + 1), bm):
        v = int(word, 16)
        for bit in range(256):
            if v >> bit & 1:
                init.append(w * 256 + bit)
    tk = rpc.batch([("eth_call", [{"to": POOL, "data": "0xf30dba93" + enc(t)}, hex(pre)]) for t in init])
    ticks = {}
    for t, r in zip(init, tk):
        gross = int(r[2:66], 16)
        net = int(r[66:130], 16)
        net = net - (1 << 256) if net >= 1 << 255 else net
        ticks[str(t)] = dict(liquidityGross=str(gross), liquidityNet=str(net))
    return dict(block=pre, sqrtPriceX96=str(sqrtp), tick=tick, liquidity=str(L),
                bitmap_range=[lo, hi], word_range=[wlo, whi], ticks=ticks)


def main():
    os.makedirs(os.path.join(RAW, "logs"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "txs"), exist_ok=True)
    a, b = WEEK
    logs = []
    for s in range(a, b + 1, CHUNK):
        e = min(s + CHUNK - 1, b)
        logs += cached(os.path.join(RAW, "logs", f"{s}-{e}.json"), lambda: rpc.call(
            "eth_getLogs", [{"address": POOL, "fromBlock": hex(s), "toBlock": hex(e),
                             "topics": [[T_SWAP, T_MINT, T_BURN]]}]))
        print(f"logs {e - a + 1}/{b - a + 1} n={len(logs)}", file=sys.stderr)
    ev = [d for d in (decode(lg) for lg in logs if not lg.get("removed")) if d]
    ev.sort(key=lambda d: (d["block"], d["log_index"]))

    swaps = [d for d in ev if d["kind"] == "swap"]
    liq = [d for d in ev if d["kind"] != "swap"]
    if "--state-only" in sys.argv:
        st = cached(os.path.join(OUT, "init_state.json"), lambda: init_state(swaps, a))
        print(f"init_ticks={len(st['ticks'])}")
        return
    big = lambda rows, cols: pa.table({c: [str(r[c]) if c in BIGS else r[c] for r in rows] for c in cols})
    BIGS = {"amount0", "amount1", "sqrtPriceX96", "liquidity", "liq_amount"}
    pq.write_table(big(swaps, ["block", "tx_index", "log_index", "tx", "sender", "recipient", "amount0", "amount1",
                               "sqrtPriceX96", "liquidity", "tick"]), os.path.join(OUT, "swaps.parquet"))
    pq.write_table(big(liq, ["block", "tx_index", "log_index", "tx", "kind", "owner", "tick_lower", "tick_upper",
                             "liq_amount", "amount0", "amount1"]), os.path.join(OUT, "liquidity.parquet"))

    # transactions touching the pool (from, to, input, gas fields)
    hashes = sorted({d["tx"] for d in ev})
    txs = []
    TXB = 500
    for k in range(0, len(hashes), TXB):
        part = hashes[k:k + TXB]
        txs += cached(os.path.join(RAW, "txs", f"{k:06d}.json"),
                      lambda: rpc.batch([("eth_getTransactionByHash", [h]) for h in part], size=50))
        print(f"txs {min(k + TXB, len(hashes))}/{len(hashes)}", file=sys.stderr)
    cols = ["hash", "blockNumber", "transactionIndex", "from", "to", "input", "gasPrice", "maxPriorityFeePerGas", "value"]
    rows = [{c: (t.get(c) or "") for c in cols} for t in txs]
    for r in rows:
        r["blockNumber"] = int(r["blockNumber"], 16)
        r["transactionIndex"] = int(r["transactionIndex"], 16)
    pq.write_table(pa.table({c: [r[c] for r in rows] for c in cols}), os.path.join(OUT, "txs.parquet"))

    st = cached(os.path.join(OUT, "init_state.json"), lambda: init_state(swaps, a))
    print(f"swaps={len(swaps)} liquidity_events={len(liq)} txs={len(txs)} init_ticks={len(st['ticks'])}")


if __name__ == "__main__":
    main()
