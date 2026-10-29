"""Properties of the Chan-Wu-Shi mechanism (arXiv 2402.09357 v3, section 3) checked on a v3 pool."""
from fractions import Fraction

from mev import mechanism, v3

L = 10**20


def pool(fee=100):
    return v3.Pool(v3.sqrt_at_tick(0), 0, L, {-5000: (L, L), 5000: (L, -L)}, fee=fee, spacing=1)


def o(i, z4o, amount, exact_in=True, limit=None):
    return dict(id=i, z4o=z4o, exact_in=exact_in, amount=amount, limit=limit)


def test_one_sided_block_equals_sequential_uniswap():
    p, q = pool(), pool()
    orders = [o(1, True, 10**17), o(2, True, 3 * 10**17), o(3, True, 10**16, exact_in=False)]
    res = mechanism.clear(p, orders)
    for x in orders:
        a0, a1 = q.swap(True, x["amount"] if x["exact_in"] else -x["amount"])
        assert res[x["id"]]["paid"] == a0 and res[x["id"]]["got"] == -a1
    assert p.state() == q.state()


def test_balanced_block_leaves_pool_and_fills_at_r0():
    p = pool()
    st = p.state()
    res = mechanism.clear(p, [o(1, True, 10**18), o(2, False, 10**18)])  # r0 = 1
    assert p.state() == st
    assert res[1]["got"] == 10**18 and res[2]["got"] == 10**18


def test_limit_worse_than_r0_dropped():
    p = pool()
    res = mechanism.clear(p, [o(1, True, 10**18, limit=Fraction(11, 10))])  # wants >= 1.1 token1 per token0
    assert res[1]["filled"] == 0


def test_phase2_stops_at_limit():
    p = pool(fee=0)
    res = mechanism.clear(p, [o(1, True, 10**20, limit=Fraction(99, 100))])
    assert 0 < res[1]["filled"] < 1
    assert abs(mechanism.r0_of(p) - Fraction(99, 100)) < Fraction(1, 10**12)
