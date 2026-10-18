"""Toy examples for the textbook, computed with the study's own tested code (mev/v3.py, mev/mechanism.py).

A Uniswap v3 position over the full tick range is exactly a constant-product pool, so the toy pool
(100 ETH and 200,000 USDC, no fee) runs through the same swap math and mechanism as the real results.
Token0 = ETH (18 decimals), token1 = USDC (6 decimals).
"""
import os
import sys
from fractions import Fraction
from math import isqrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import mechanism, v3

E, U = 10**18, 10**6
X0, Y0 = 100 * E, 200_000 * U          # pool reserves
VICTIM_IN = 20_000 * U                   # victim pays 20,000 USDC for ETH
VICTIM_MIN = 88 * E // 10                 # victim accepts at least 8.8 ETH (about 3% slippage)
VICTIM_MARGINAL = 2_500                  # mechanism example: worst marginal price the victim accepts, USDC/ETH
LO, HI = -887270, 887270                 # full range at tick spacing 10


def pool():
    L = isqrt(X0 * Y0)
    sp = isqrt(Y0 * (1 << 192) // X0)
    return v3.Pool(sp, v3.tick_at_sqrt(sp), L, {LO: (L, L), HI: (L, -L)}, fee=0, spacing=10)


def buy_eth(p, usdc):
    a0, a1 = p.swap(False, usdc)
    return -a0                            # ETH out


def sell_eth(p, eth):
    a0, a1 = p.swap(True, eth)
    return -a1                            # USDC out


def price(p):
    return float(mechanism.r0_of(p)) * E / U  # USDC per ETH


def no_attack():
    p = pool()
    out = buy_eth(p, VICTIM_IN)
    return dict(victim_eth=out, price_after=price(p))


def max_front_run():
    """Largest front-run (USDC) that still leaves the victim at least VICTIM_MIN ETH."""
    lo, hi = 0, 200_000 * U
    while hi - lo > U // 100:
        mid = (lo + hi) // 2
        p = pool()
        buy_eth(p, mid)
        if buy_eth(p, VICTIM_IN) >= VICTIM_MIN:
            lo = mid
        else:
            hi = mid
    return lo


def sandwich(a):
    p = pool()
    path = [("start", price(p))]
    f_eth = buy_eth(p, a)
    path.append(("front-run", price(p)))
    v_eth = buy_eth(p, VICTIM_IN)
    path.append(("victim", price(p)))
    b_usdc = sell_eth(p, f_eth)
    path.append(("back-run", price(p)))
    return dict(front_in=a, front_eth=f_eth, victim_eth=v_eth, back_usdc=b_usdc,
                attacker_profit_usdc=b_usdc - a, path=path)


def mech(a, front_eth, victim_first, marginal=None, back_usdc=None):
    """Same three orders cleared by Chan-Wu-Shi. Attacker legs carry no limit; the victim states a marginal
    limit of VICTIM_MARGINAL USDC per ETH, generous enough to fill completely."""
    p = pool()
    vlim = Fraction(VICTIM_MARGINAL * U, E) if marginal is None else marginal
    # back_usdc given: each attacker leg's limit is its own executed average price (the study's static rule)
    flim = Fraction(a, front_eth) if back_usdc else None
    blim = Fraction(back_usdc, front_eth) if back_usdc else None
    F = dict(id="F", z4o=False, exact_in=True, amount=a, limit=flim)
    V = dict(id="V", z4o=False, exact_in=True, amount=VICTIM_IN, limit=vlim)
    B = dict(id="B", z4o=True, exact_in=True, amount=front_eth, limit=blim)
    order = [V, F, B] if victim_first else [F, V, B]
    r = mechanism.clear(p, order)
    r0 = Fraction(Y0, X0)
    atk_eth = r["F"]["got"] - r["B"]["paid"]
    atk_usdc = r["B"]["got"] - r["F"]["paid"]
    return dict(victim_eth=r["V"]["got"], victim_filled=r["V"]["filled"],
                attacker_net_usdc=atk_usdc + atk_eth * r0, price_after=price(p),
                phase1_eth=min(Fraction(front_eth), Fraction(a) / r0 + Fraction(VICTIM_IN) / r0))


def all_examples():
    na = no_attack()
    a = max_front_run()
    s = sandwich(a)
    m_front = mech(a, s["front_eth"], victim_first=False)
    m_vfirst = mech(a, s["front_eth"], victim_first=True)
    out = dict(no_attack=na, front_in=a, sandwich=s, mech_front_first=m_front, mech_victim_first=m_vfirst)
    # checks: the attack is profitable in the continuous market and not under the mechanism
    assert s["victim_eth"] >= VICTIM_MIN and s["attacker_profit_usdc"] > 0
    assert m_front["attacker_net_usdc"] <= 0 and m_vfirst["attacker_net_usdc"] <= 0
    assert m_vfirst["victim_eth"] >= na["victim_eth"] - E // 10**6
    # average-vs-marginal: the same victim with its minimum output read as a marginal limit (the study's rule)
    out["mech_executed_limits"] = mech(a, s["front_eth"], victim_first=False, back_usdc=s["back_usdc"])
    assert out["mech_executed_limits"]["attacker_net_usdc"] <= 0
    out["avg_as_marginal"] = mech(a, s["front_eth"], victim_first=True, marginal=Fraction(VICTIM_IN, VICTIM_MIN))
    return out


if __name__ == "__main__":
    ex = all_examples()
    na, s = ex["no_attack"], ex["sandwich"]
    print(f"no attack: victim gets {na['victim_eth'] / E:.4f} ETH, price after {na['price_after']:.2f}")
    print(f"front-run {s['front_in'] / U:,.2f} USDC -> {s['front_eth'] / E:.4f} ETH")
    print(f"victim gets {s['victim_eth'] / E:.4f} ETH (min 8.8); back-run returns {s['back_usdc'] / U:,.2f} USDC")
    print(f"attacker profit {s['attacker_profit_usdc'] / U:,.2f} USDC; path {[(k, round(v, 1)) for k, v in s['path']]}")
    for k in ("mech_front_first", "mech_victim_first", "mech_executed_limits", "avg_as_marginal"):
        m = ex[k]
        print(f"{k}: victim {float(m['victim_eth']) / E:.4f} ETH filled {float(m['victim_filled']):.3f}, "
              f"attacker net {float(m['attacker_net_usdc']) / U:,.2f} USDC, price after {m['price_after']:.2f}")
