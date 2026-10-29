"""Property-based tests (Hypothesis) of mechanism.clear on random v3 pools and random order sets."""
from fractions import Fraction

import pytest
from hypothesis import assume, event, example, given, strategies as st

from mev import mechanism, v3

Q192 = 1 << 192


# -- pools -----------------------------------------------------------------------------------------
class RecordingPool(v3.Pool):
    """Logs every swap clear() makes, tagged with the order whose fields clear() read last."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []

    def swap(self, z4o, amount_specified, limit=None):
        before = self.sqrt_price
        a0, a1 = super().swap(z4o, amount_specified, limit)
        self.calls.append(dict(order=SpyOrder.last, z4o=z4o, limit_arg=limit, before=before, after=self.sqrt_price,
                               a0=a0, a1=a1))
        return a0, a1


class SpyOrder(dict):
    last = None

    def __getitem__(self, key):
        SpyOrder.last = dict.__getitem__(self, "id")
        return dict.__getitem__(self, key)


@st.composite
def pool_specs(draw):
    """(sqrt_price, tick, fee, spacing, positions) with positions a list of (lower, upper, liquidity)."""
    spacing = draw(st.sampled_from([10, 60, 200]))
    fee = draw(st.sampled_from([0, 100, 500, 3000, 10000]))
    tick = draw(st.integers(-120_000, 120_000))
    sp = draw(st.integers(v3.sqrt_at_tick(tick), v3.sqrt_at_tick(tick + 1) - 1))
    liq = st.one_of(st.integers(10**6, 10**24), st.sampled_from([10**12, 10**18, 10**20]))
    positions = []
    for i in range(draw(st.integers(1, 4))):
        lower = (tick + draw(st.integers(-60_000, 60_000))) // spacing * spacing
        upper = lower + spacing * draw(st.integers(1, 60_000 // spacing + 1))
        positions.append((lower, upper, draw(liq)))
    # a wide position around the price keeps swaps short (without it, a drained pool is walked word by word to the
    # edge of the tick range)
    lo = (tick - draw(st.integers(1, 80_000))) // spacing * spacing
    positions.append((lo, (tick + draw(st.integers(1, 80_000))) // spacing * spacing + spacing, draw(liq)))
    return sp, tick, fee, spacing, positions


def make_pool(spec, cls=v3.Pool):
    sp, tick, fee, spacing, positions = spec
    p = cls(sp, tick, 0, {}, fee, spacing)
    for lower, upper, liq in positions:
        p.modify(lower, upper, liq)
    return p


def reserves(spec, sp):
    """Exact token0 and token1 held by the pool's positions at sqrtPriceX96 sp."""
    x = y = Fraction(0)
    for lower, upper, liq in spec[4]:
        a, b = v3.sqrt_at_tick(lower), v3.sqrt_at_tick(upper)
        if sp <= a:
            x += Fraction(liq * v3.Q96 * (b - a), a * b)
        elif sp < b:
            x += Fraction(liq * v3.Q96 * (b - sp), sp * b)
            y += Fraction(liq * (sp - a), v3.Q96)
        else:
            y += Fraction(liq * (b - a), v3.Q96)
    return x, y


# -- orders ----------------------------------------------------------------------------------------
amounts = st.builds(lambda m, e: m * 10**e, st.integers(1, 999), st.integers(0, 20))
limit_factors = st.one_of(st.none(), st.integers(1, 40_000).map(lambda n: Fraction(n, 10_000) + Fraction(1, 2)),
                          st.integers(9_950, 10_050).map(lambda n: Fraction(n, 10_000)))


def make_order(i, z4o, exact_in, amount, factor, r0):
    return SpyOrder(id=i, z4o=z4o, exact_in=exact_in, amount=amount, limit=None if factor is None else r0 * factor)


@st.composite
def blocks(draw, min_orders=1, max_orders=7):
    """(pool spec, orders in tie-break order, fee_phase1). Limits are scaled off the pool's starting price r0."""
    spec = draw(pool_specs())
    r0 = mechanism.r0_of(make_pool(spec))
    n = draw(st.integers(min_orders, max_orders))
    orders = [make_order(i, draw(st.booleans()), draw(st.booleans()), draw(amounts), draw(limit_factors), r0)
              for i in range(n)]
    return spec, orders, draw(st.booleans())


def run(spec, orders, fee_phase1=False):
    """clear() on a fresh pool. Blocks that hit the drained-pool crash (see test_drained_pool_does_not_crash_clear)
    are skipped, and counted in Hypothesis's event statistics; any other exception fails the property."""
    pool = make_pool(spec, RecordingPool)
    r0 = mechanism.r0_of(pool)
    try:
        return pool, r0, mechanism.clear(pool, orders, fee_phase1=fee_phase1)
    except AssertionError:
        if pool.sqrt_price not in (v3.MIN_SQRT_RATIO + 1, v3.MAX_SQRT_RATIO - 1):
            raise
        event("skipped: pool drained to its price bound, then another unlimited order in the same direction")
        assume(False)


def value_at_r0(order, r, r0):
    """What the order got minus what it paid, in token1, with token0 valued at r0."""
    return r["got"] - r["paid"] * r0 if order["z4o"] else r["got"] * r0 - r["paid"]


# -- properties ------------------------------------------------------------------------------------
@given(blocks(max_orders=4), st.data())
def test_sandwich_not_profitable_any_order(block, data):
    """Theorem 3.1 (arbitrage resilience), generalised: random pool, a front-run buy and a back-run sell with random
    size, exact-in/out and limit, a random victim and extra orders, in any tie-break order. The attacker's two legs
    net <= 0 at r0."""
    spec, extras, fee_phase1 = block
    r0 = mechanism.r0_of(make_pool(spec))
    front = make_order("F", False, data.draw(st.booleans()), data.draw(amounts), data.draw(limit_factors), r0)
    back = make_order("B", True, data.draw(st.booleans()), data.draw(amounts), data.draw(limit_factors), r0)
    victim = make_order("V", False, data.draw(st.booleans()), data.draw(amounts), data.draw(limit_factors), r0)
    orders = data.draw(st.permutations([front, back, victim] + extras))
    _, r0, res = run(spec, orders, fee_phase1)
    net = sum((value_at_r0(o, res[o["id"]], r0) for o in (front, back)), Fraction(0))
    assert net <= 0, (net, res["F"], res["B"])


@given(blocks())
def test_no_order_executes_better_than_r0(block):
    spec, orders, fee_phase1 = block
    _, r0, res = run(spec, orders, fee_phase1)
    for o in orders:
        assert value_at_r0(o, res[o["id"]], r0) <= 0, (o, res[o["id"]])


@given(blocks())
def test_fills_stay_within_the_order_and_its_limit_at_r0(block):
    spec, orders, _ = block
    _, r0, res = run(spec, orders)
    for o in orders:
        r = res[o["id"]]
        assert 0 <= r["filled"] <= 1
        assert r["paid"] >= 0 and r["got"] >= 0
        assert (r["paid"] if o["exact_in"] else r["got"]) <= o["amount"]
        if o["limit"] is not None and not (o["limit"] <= r0 if o["z4o"] else o["limit"] >= r0):
            assert r["filled"] == 0 and r["paid"] == 0 and r["got"] == 0  # limit worse than r0: dropped


def limit_overshoots(block, z4o):
    """Phase-2 swaps in one direction whose end price is past the order's limit, as (end sqrtP, limit) pairs, and the
    same pairs when the end price is moved back by one sqrtPriceX96 unit."""
    spec, orders, fee_phase1 = block
    pool, _, _ = run(spec, orders, fee_phase1)
    by_id = {o["id"]: o for o in orders}
    strict, within_one_unit = [], []
    for c in pool.calls:
        limit = dict.__getitem__(by_id[c["order"]], "limit")
        if limit is None or c["z4o"] != z4o:
            continue
        step = 1 if z4o else -1  # toward the start price
        strict.append(Fraction(c["after"] ** 2, Q192) < limit if z4o else Fraction(c["after"] ** 2, Q192) > limit)
        within_one_unit.append(Fraction((c["after"] + step) ** 2, Q192) < limit if z4o
                               else Fraction((c["after"] + step) ** 2, Q192) > limit)
    return any(strict), any(within_one_unit)


BUY_AT_R0 = (((1 << 96), 0, 0, 10, [(-1000, 1000, 10**20)]),
             [SpyOrder(id=0, z4o=False, exact_in=True, amount=10**19, limit=Fraction(1))], False)
SELL_BELOW_R0 = (((1 << 96), 0, 0, 10, [(-1000, 1000, 10**20)]),
                 [SpyOrder(id=0, z4o=True, exact_in=True, amount=10**19, limit=Fraction(99, 100))], False)


@given(blocks())
def test_phase2_ends_within_one_sqrt_unit_of_every_limit(block):
    """The weaker form of the next two tests: the end price is never more than 1 unit of sqrtPriceX96 past a limit."""
    assert not any(limit_overshoots(block, True)[1:] + limit_overshoots(block, False)[1:])


@pytest.mark.xfail(strict=True, reason="finding: a buy is allowed to end one sqrtPriceX96 unit above its limit, "
                                       "because clear() passes floor(sqrt(limit)) + 1 as the swap's price limit")
@example(BUY_AT_R0)
@given(blocks())
def test_phase2_never_moves_the_price_above_a_buy_limit(block):
    assert not limit_overshoots(block, False)[0]


@pytest.mark.xfail(strict=True, reason="finding: a sell is allowed to end one sqrtPriceX96 unit below its limit, "
                                       "because clear() passes floor(sqrt(limit)) as the swap's price limit")
@example(SELL_BELOW_R0)
@given(blocks())
def test_phase2_never_moves_the_price_below_a_sell_limit(block):
    assert not limit_overshoots(block, True)[0]


FEE_ON_FULL_FILL = (((1 << 96), 0, 3000, 10, [(-1000, 1000, 10**20)]),
                    [SpyOrder(id=1, z4o=True, exact_in=True, amount=10**18, limit=None),
                     SpyOrder(id=2, z4o=False, exact_in=True, amount=10**18, limit=None)], True)


@pytest.mark.xfail(strict=True, reason="finding: with fee_phase1, a fully filled exact-in order pays amount / (1 - fee), "
                                       "more than the amount it offered")
@example(FEE_ON_FULL_FILL)
@given(blocks())
def test_exact_in_order_never_pays_more_than_its_amount_with_phase1_fee(block):
    spec, orders, _ = block
    _, _, res = run(spec, orders, fee_phase1=True)
    for o in orders:
        if o["exact_in"]:
            assert res[o["id"]]["paid"] <= o["amount"], (o, res[o["id"]])


@given(blocks())
def test_clear_conserves_tokens(block):
    spec, orders, _ = block
    pool, _, res = run(spec, orders)
    paid0 = paid1 = Fraction(0)
    for o in orders:
        r = res[o["id"]]
        if o["z4o"]:
            paid0 += r["paid"]
            paid1 -= r["got"]
        else:
            paid1 += r["paid"]
            paid0 -= r["got"]
    # orders trade with each other at r0 in phase 1 and with the pool in phase 2: users' net flow is the pool's
    assert (paid0, paid1) == (sum(c["a0"] for c in pool.calls), sum(c["a1"] for c in pool.calls))
    # and the pool's own books agree: it never takes in less, or pays out more, than the exact reserve change
    x0, y0 = reserves(spec, spec[0])
    x1, y1 = reserves(spec, pool.sqrt_price)
    assert x1 - x0 <= paid0 and y1 - y0 <= paid1
    if spec[2] == 0:  # no fee: the gap is rounding only, at most 2 units per token per swap step
        spacing, positions = spec[3], spec[4]
        steps = sum(abs(v3.tick_at_sqrt(c["after"]) - v3.tick_at_sqrt(c["before"])) // (256 * spacing)
                    + 2 * len(positions) + 3 for c in pool.calls)  # one step per tick-bitmap word, plus tick crossings
        assert paid0 - (x1 - x0) <= 2 * steps and paid1 - (y1 - y0) <= 2 * steps


@given(blocks())
def test_phase1_fee_never_creates_tokens(block):
    """With fee_phase1 the users pay the pool fee on phase-1 input, so they pay in at least what they take out."""
    spec, orders, _ = block
    pool, _, res = run(spec, orders, fee_phase1=True)
    flow0 = flow1 = Fraction(0)
    for o in orders:
        r = res[o["id"]]
        if o["z4o"]:
            flow0, flow1 = flow0 + r["paid"], flow1 - r["got"]
        else:
            flow0, flow1 = flow0 - r["got"], flow1 + r["paid"]
    assert flow0 >= sum(c["a0"] for c in pool.calls) and flow1 >= sum(c["a1"] for c in pool.calls)


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="finding: clear() calls Pool.swap with its default price limit after an earlier order drained "
                          "the pool to that limit, and the swap precondition fails")
def test_drained_pool_does_not_crash_clear():
    """Two unlimited sells, the first bigger than all the liquidity: the pool slides to MIN_SQRT_RATIO + 1 and the second
    order's swap asserts MIN_SQRT_RATIO < limit < sqrt_price. Valid orders should fill 0 here, not raise."""
    spec = (v3.sqrt_at_tick(0), 0, 0, 10, [(-10, 10, 10**6)])
    pool = make_pool(spec)
    orders = [dict(id=i, z4o=True, exact_in=True, amount=10**9, limit=None) for i in range(2)]
    res = mechanism.clear(pool, orders)
    assert res[1]["paid"] == 0 and res[1]["got"] == 0
