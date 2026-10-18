import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import v3


def test_tick_bounds_and_zero():
    assert v3.sqrt_at_tick(0) == v3.Q96
    assert v3.sqrt_at_tick(v3.MIN_TICK) == v3.MIN_SQRT_RATIO
    assert v3.sqrt_at_tick(v3.MAX_TICK) == v3.MAX_SQRT_RATIO


def test_tick_inverse():
    for t in (-887272, -200000, -195000, -1, 0, 1, 50, 123456, 887271):
        sp = v3.sqrt_at_tick(t)
        assert v3.tick_at_sqrt(sp) == t
        if t < 887271:
            assert v3.tick_at_sqrt(sp + 1) == t


def test_swap_roundtrip_single_range():
    L = 10**18
    p = v3.Pool(v3.sqrt_at_tick(0), 0, L, {-600: (L, L), 600: (L, -L)}, fee=3000, spacing=1)
    a0, a1 = p.quote(True, 10**15)
    assert a0 == 10**15 and a1 < 0
    # exact output of the same amount1 needs no more than the exact-input amount0
    b0, b1 = p.quote(True, a1)
    assert b1 == a1 and b0 <= a0


def test_crossing_removes_liquidity():
    L = 10**18
    p = v3.Pool(v3.sqrt_at_tick(0), 0, L, {-10: (L, L), 10: (L, -L)}, fee=0, spacing=1)
    p.swap(True, 10**18)  # far more than the range holds
    assert p.liquidity == 0 and p.tick < -10
