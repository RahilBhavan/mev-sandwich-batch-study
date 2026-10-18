"""Per-block two-phase clearing from Chan, Wu, Shi, "Mechanism Design for Automated Market Makers" (AFT 2025,
arXiv 2402.09357 v3, section 3.1, Figure 1), run on a Uniswap v3 pool.

Order: dict(id, z4o, exact_in, amount, limit) where
  z4o      True if the order pays token0 and receives token1
  exact_in amount is the input amount (True) or the desired output amount (False)
  limit    worst acceptable marginal price as raw token1 per raw token0 (Fraction), or None for no limit

1. r0 = the pool's marginal price at the start of the block. Orders whose limit is worse than r0 are dropped.
2. Every order's size is measured in token0 at r0. The side with less volume is the minority.
3. Phase 1: the minority side fills completely at r0 against the dominant side, taken in tie-break order;
   the boundary order is split. The pool does not move.
4. Phase 2: the rest of the dominant side executes one order at a time on the pool, each until its amount
   is filled or the marginal price reaches its limit (v3 sqrtPriceLimitX96). Partial fills are allowed.

fee_phase1: charge the pool fee on phase-1 input (the paper's model has no fee; the pool fee applies in phase 2).
Returns {id: dict(paid, got, filled)} as exact numbers: paid/got in the order's input/output token,
filled = fraction of amount.
"""
from fractions import Fraction
from math import isqrt

from mev import v3


def sqrt_price_of(p):
    """sqrtPriceX96 for a Fraction price p (raw token1 per raw token0), rounded down."""
    return isqrt(p.numerator * (1 << 192) // p.denominator)


def r0_of(pool):
    return Fraction(pool.sqrt_price * pool.sqrt_price, 1 << 192)


def _ok_vs_r0(o, r0):
    if o["limit"] is None:
        return True
    return o["limit"] <= r0 if o["z4o"] else o["limit"] >= r0


def _size0(o, r0):
    """Order size in token0 at r0."""
    if o["z4o"]:
        return Fraction(o["amount"]) if o["exact_in"] else Fraction(o["amount"]) / r0
    return Fraction(o["amount"]) / r0 if o["exact_in"] else Fraction(o["amount"])


def clear(pool, orders, fee_phase1=False):
    """Mutates pool (phase 2 swaps). orders must already be in tie-break order."""
    r0 = r0_of(pool)
    fee = Fraction(pool.fee, 1_000_000) if fee_phase1 else Fraction(0)
    res = {o["id"]: dict(paid=0, got=0, filled=Fraction(0)) for o in orders}
    live = [o for o in orders if _ok_vs_r0(o, r0)]
    sell0 = [o for o in live if o["z4o"]]
    buy0 = [o for o in live if not o["z4o"]]
    S = sum((_size0(o, r0) for o in sell0), Fraction(0))
    D = sum((_size0(o, r0) for o in buy0), Fraction(0))
    minority, dominant, m = (sell0, buy0, S) if S <= D else (buy0, sell0, D)

    def fill_at_r0(o, q0):
        """Fill q0 token0-equivalent of order o at r0 (with optional fee on input)."""
        if o["z4o"]:   # pays token0, gets token1
            paid, got = q0 / (1 - fee), q0 * r0
        else:          # pays token1, gets token0
            paid, got = q0 * r0 / (1 - fee), q0
        r = res[o["id"]]
        r["paid"] += paid
        r["got"] += got
        r["filled"] += q0 / _size0(o, r0)

    for o in minority:
        fill_at_r0(o, _size0(o, r0))
    left = m
    queue = []
    for o in dominant:
        size = _size0(o, r0)
        take = min(size, left)
        if take > 0:
            fill_at_r0(o, take)
            left -= take
        if take < size:
            queue.append(o)

    # phase 2: remaining dominant orders along the curve
    for o in queue:
        r = res[o["id"]]
        frac_left = 1 - r["filled"]
        rem = int(o["amount"] * frac_left)  # floor: never exceed the order
        if rem <= 0:
            continue
        lim = None
        if o["limit"] is not None:
            lim = sqrt_price_of(o["limit"])
            if o["z4o"]:
                lim = max(lim, v3.MIN_SQRT_RATIO + 1)
                if lim >= pool.sqrt_price:
                    continue
            else:
                lim = min(lim + 1, v3.MAX_SQRT_RATIO - 1)
                if lim <= pool.sqrt_price:
                    continue
        a0, a1 = pool.swap(o["z4o"], rem if o["exact_in"] else -rem, lim)
        paid, got = (a0, -a1) if o["z4o"] else (a1, -a0)
        r["paid"] += paid
        r["got"] += got
        spec = paid if o["exact_in"] else got
        r["filled"] += Fraction(spec, o["amount"])
    return res
