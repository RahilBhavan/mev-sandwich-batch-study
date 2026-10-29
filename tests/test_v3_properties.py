"""Property-based tests (Hypothesis) of the exact integer math in mev/v3.py."""
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest
from hypothesis import assume, given, strategies as st

from mev import v3

uint256 = st.one_of(
    st.integers(0, v3.U256 - 1),
    st.integers(0, 1000),
    st.builds(lambda k, e: (1 << k) + e, st.integers(0, 255), st.integers(0, 1)),
    st.builds(lambda k, e: (1 << k) - e, st.integers(1, 256), st.integers(0, 1)),
)
divisor = uint256.filter(lambda d: d > 0)
ticks = st.integers(v3.MIN_TICK, v3.MAX_TICK)
below_max_tick = st.integers(v3.MIN_TICK, v3.MAX_TICK - 1)  # tick_at_sqrt needs sqrtP < MAX_SQRT_RATIO


@st.composite
def sqrt_prices(draw):
    """Any sqrtPriceX96 in [MIN_SQRT_RATIO, MAX_SQRT_RATIO), spread evenly across ticks, biased to tick edges."""
    t = draw(below_max_tick)
    lo, hi = v3.sqrt_at_tick(t), v3.sqrt_at_tick(t + 1) - 1
    return draw(st.one_of(st.integers(lo, hi), st.sampled_from([lo, hi])))


# -- TickMath --------------------------------------------------------------------------------------
@given(below_max_tick)
def test_tick_roundtrip_over_full_range(t):
    assert v3.tick_at_sqrt(v3.sqrt_at_tick(t)) == t


@given(sqrt_prices())
def test_sqrt_roundtrip_brackets_price(s):
    t = v3.tick_at_sqrt(s)
    assert v3.sqrt_at_tick(t) <= s < v3.sqrt_at_tick(t + 1)


@given(below_max_tick)
def test_sqrt_at_tick_strictly_increasing(t):
    assert v3.sqrt_at_tick(t) < v3.sqrt_at_tick(t + 1)


@given(ticks)
def test_sqrt_at_tick_close_to_exact_power(t):
    """sqrt(1.0001^t) * 2^96 within 1 unit plus 2^-60 relative, against a Decimal oracle independent of the magic
    constants. The 2^-60 is a loose sanity bound chosen here, not a Uniswap guarantee: the product is kept in Q128
    and shrinks with |t|, so relative accuracy degrades toward the ends of the range (about 2^-79 seen at t=672614)."""
    with localcontext() as ctx:
        ctx.prec = 120
        exact = (Decimal("1.0001") ** (Decimal(t) / 2)) * (1 << 96)
        got = Decimal(v3.sqrt_at_tick(t))
        assert abs(got - exact) <= 1 + exact / (1 << 60)


def test_tick_at_sqrt_domain_matches_uniswap():
    with pytest.raises(AssertionError):
        v3.tick_at_sqrt(v3.MAX_SQRT_RATIO)
    with pytest.raises(AssertionError):
        v3.tick_at_sqrt(v3.MIN_SQRT_RATIO - 1)
    with pytest.raises(AssertionError):
        v3.sqrt_at_tick(v3.MAX_TICK + 1)


# -- mulDiv ----------------------------------------------------------------------------------------
@given(uint256, uint256, divisor)
def test_mul_div_matches_exact_floor_and_ceil(a, b, d):
    exact = Fraction(a * b, d)
    down, up = v3.mul_div(a, b, d), v3.mul_div_up(a, b, d)
    assert down == exact.__floor__()
    assert up == exact.__ceil__()
    assert up - down in (0, 1)
    assert (up == down) == (a * b % d == 0)


@given(uint256, divisor)
def test_div_up_is_ceil(a, d):
    assert v3.div_up(a, d) == Fraction(a, d).__ceil__()


# -- SqrtPriceMath deltas --------------------------------------------------------------------------
liquidity = st.one_of(st.integers(1, (1 << 128) - 1), st.integers(1, 10**6), st.integers(10**15, 10**25))


@given(sqrt_prices(), sqrt_prices(), liquidity)
def test_amount_deltas_round_toward_the_pool(a, b, L):
    lo, hi = min(a, b), max(a, b)
    exact0 = Fraction(L * v3.Q96 * (hi - lo), lo * hi)
    exact1 = Fraction(L * (hi - lo), v3.Q96)
    for x, y in ((v3.amount0_delta(a, b, L, False), v3.amount0_delta(a, b, L, True)),):
        assert x <= exact0 <= y and y - x <= 2
    assert v3.amount0_delta(a, b, L, True) == v3.amount0_delta(b, a, L, True)
    assert v3.amount1_delta(a, b, L, False) == exact1.__floor__()
    assert v3.amount1_delta(a, b, L, True) == exact1.__ceil__()


# -- SwapMath --------------------------------------------------------------------------------------
fees = st.one_of(st.sampled_from([0, 100, 500, 3000, 10000]), st.integers(0, 999_999))
magnitudes = st.one_of(st.integers(1, 10**6), st.integers(1, 10**18), st.integers(1, 1 << 128), st.integers(1, (1 << 255) - 1))
amounts_specified = st.builds(lambda m, neg: -m if neg else m, magnitudes, st.booleans())


@st.composite
def swap_steps(draw):
    cur = draw(sqrt_prices())
    close = st.builds(lambda d: min(max(cur + d, v3.MIN_SQRT_RATIO), v3.MAX_SQRT_RATIO - 1),
                      st.integers(-1000, 1000) | st.integers(-(1 << 64), 1 << 64))
    target = draw(st.one_of(sqrt_prices(), close))
    assume(target != cur)
    return cur, target, draw(liquidity), draw(amounts_specified), draw(fees)


@given(swap_steps())
def test_compute_swap_step_bounds(step):
    cur, target, L, remaining, fee = step
    z4o = cur >= target
    nxt, amount_in, amount_out, fee_amt = v3.compute_swap_step(cur, target, L, remaining, fee)
    # never overshoots the target, never moves against the swap direction
    assert target <= nxt <= cur if z4o else cur <= nxt <= target
    # never beats the exact price curve: pays at least, receives at most, what x*y=k says for cur -> nxt
    lo, hi = min(cur, nxt), max(cur, nxt)
    exact_x = Fraction(L * v3.Q96 * (hi - lo), lo * hi)   # token0 moved
    exact_y = Fraction(L * (hi - lo), v3.Q96)             # token1 moved
    exact_in, exact_out = (exact_x, exact_y) if z4o else (exact_y, exact_x)
    assert amount_out <= exact_out
    assert amount_in >= exact_in
    assert amount_in >= 0 and amount_out >= 0 and fee_amt >= 0
    # the fee covers at least fee/(1-fee) of the input
    assert fee_amt * (1_000_000 - fee) >= amount_in * fee
    if remaining > 0:
        assert amount_in + fee_amt <= remaining
        if nxt != target:
            assert amount_in + fee_amt == remaining
    else:
        assert amount_out <= -remaining
