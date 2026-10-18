"""USD value of raw token amounts at a given block.

Token1 of the main pool is USDT, taken as $1. For other pools, WETH is valued at the WETH/USDT pool's last
price at or before the block, from the main pool's ingested swaps (data/week/swaps.parquet).
"""
import bisect
import os

import pyarrow.parquet as pq

from mev import v3
from mev.pool import DEC0, DEC1, TOKEN0_ADDR, TOKEN1_ADDR, WETH_ADDR

_ETH = None


def _eth_table(d="data/week"):
    global _ETH
    if _ETH is None:
        t = pq.read_table(os.path.join(d, "swaps.parquet"), columns=["block", "log_index", "sqrtPriceX96"]).to_pylist()
        t.sort(key=lambda r: (r["block"], r["log_index"]))
        blocks, prices = [], []
        for r in t:
            p = (int(r["sqrtPriceX96"]) / v3.Q96) ** 2 * 1e18 / 1e6   # USDT per ETH
            if blocks and blocks[-1] == r["block"]:
                prices[-1] = p
            else:
                blocks.append(r["block"])
                prices.append(p)
        _ETH = (blocks, prices)
    return _ETH


def eth_usd(block):
    """ETH price in USD at the start of `block` (last WETH/USDT swap before it)."""
    blocks, prices = _eth_table()
    i = bisect.bisect_left(blocks, block) - 1
    return prices[max(i, 0)]


def usd_per_raw(token_addr, block, r0=None):
    """USD per raw unit of a pool token. r0 = raw token1 per raw token0 at the block start."""
    if token_addr == "0xdac17f958d2ee523a2206206994597c13d831ec7":
        return 1e-6
    if token_addr == WETH_ADDR:
        return eth_usd(block) / 1e18
    if token_addr == TOKEN0_ADDR:            # priced through token1 at the pool's own price
        return float(r0) * usd_per_raw(TOKEN1_ADDR, block)
    raise ValueError(token_addr)
