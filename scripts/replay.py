"""Gate for the simulator: replay every event of the week and check each swap reproduces exactly.

For each observed swap the order type is unknown, so four hypotheses are tried in turn:
exact input, exact output, and each of those stopped by a price limit at the observed final price.
A swap matches when amounts and the post-swap (sqrtPrice, liquidity, tick) all equal the event.

usage: python scripts/replay.py [DATADIR]
writes DATADIR/replay.parquet and prints a summary
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pyarrow as pa
import pyarrow.parquet as pq

from mev import data

D = sys.argv[1] if len(sys.argv) > 1 else "data/week"


def try_modes(pool, s):
    z4o = s["amount0"] > 0
    a_in, a_out = (s["amount0"], -s["amount1"]) if z4o else (s["amount1"], -s["amount0"])
    post = (s["sqrtPriceX96"], s["tick"], s["liquidity"])
    obs = (s["amount0"], s["amount1"])
    tries = [("exact_in", a_in, None), ("exact_out", -a_out, None)]
    if post[0] != pool.sqrt_price and (post[0] < pool.sqrt_price) == z4o:
        tries += [("limit_in", a_in + 1, post[0]), ("limit_out", -(a_out + 1), post[0])]
    hits = []
    for mode, amt, lim in tries:
        if amt == 0:
            continue
        st = pool.state()
        try:
            res = pool.swap(z4o, amt, lim)
            ok = res == obs and pool.state() == post
        except AssertionError:
            ok = False
        pool.set_state(st)
        if ok:
            hits.append(mode)
    return z4o, hits


def main():
    events, _, st = data.load(D)
    pool = data.initial_pool(st)
    rows, stats = [], collections.Counter()
    for e in events:
        if e["kind"] == "swap":
            if e["amount0"] == 0 and e["amount1"] == 0:
                stats["zero"] += 1
                continue
            pre = pool.state()
            z4o, hits = try_modes(pool, e)
            stats[hits[0] if hits else "MISMATCH"] += 1
            if len(hits) > 1:
                stats["ambiguous"] += 1
            rows.append(dict(block=e["block"], log_index=e["log_index"], tx=e["tx"], z4o=z4o,
                             mode=hits[0] if hits else "", modes=",".join(hits),
                             pre_sqrt=str(pre[0]), pre_tick=pre[1], pre_liquidity=str(pre[2])))
            # resync to the observed post-state (a no-op when the swap matched)
            pool.set_state((e["sqrtPriceX96"], e["tick"], e["liquidity"]))
        else:
            sign = 1 if e["kind"] == "mint" else -1
            pool.modify(e["tick_lower"], e["tick_upper"], sign * e["liq_amount"])
    pq.write_table(pa.Table.from_pylist(rows), os.path.join(D, "replay.parquet"))
    n = len(rows)
    print(f"swaps={n} matched={n - stats['MISMATCH']} ({100 * (n - stats['MISMATCH']) / n:.3f}%)")
    print(dict(stats))
    bad = [r for r in rows if not r["mode"]][:10]
    for r in bad:
        print("mismatch", r["block"], r["log_index"], r["tx"])


if __name__ == "__main__":
    main()
