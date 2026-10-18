"""Load the ingested week into plain Python structures with integer amounts."""
import json
import os

import pyarrow.parquet as pq

from mev import v3
from mev.pool import FEE_PIPS, TICK_SPACING

BIG = {"amount0", "amount1", "sqrtPriceX96", "liquidity", "liq_amount"}


def _rows(path):
    t = pq.read_table(path).to_pylist()
    for r in t:
        for k in BIG & r.keys():
            r[k] = int(r[k])
    return t


def load(d="data/week"):
    swaps = _rows(os.path.join(d, "swaps.parquet"))
    for s in swaps:
        s["kind"] = "swap"
    liq = _rows(os.path.join(d, "liquidity.parquet"))
    events = sorted(swaps + liq, key=lambda e: (e["block"], e["log_index"]))
    tp = os.path.join(d, "txs.parquet")
    txs = {t["hash"]: t for t in pq.read_table(tp).to_pylist()} if os.path.exists(tp) else {}
    st = json.load(open(os.path.join(d, "init_state.json")))
    return events, txs, st


def initial_pool(st):
    ticks = {int(t): (int(v["liquidityGross"]), int(v["liquidityNet"])) for t, v in st["ticks"].items()}
    return v3.Pool(int(st["sqrtPriceX96"]), st["tick"], int(st["liquidity"]), ticks, FEE_PIPS, TICK_SPACING)


def price(sqrt_price):
    """Raw token1 per raw token0 as a float."""
    return (sqrt_price / v3.Q96) ** 2
