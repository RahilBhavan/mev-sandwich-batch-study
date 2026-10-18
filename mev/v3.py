"""Exact Python port of Uniswap v3 swap math (TickMath, SqrtPriceMath, SwapMath, TickBitmap, Pool.swap).

Integers only. 256-bit overflow branches in SqrtPriceMath are emulated because they change rounding.
The protocol fee is ignored: it splits the LP fee and does not change swap amounts.
"""
import bisect

Q96 = 1 << 96
U256 = 1 << 256
U160_MAX = (1 << 160) - 1
MIN_TICK, MAX_TICK = -887272, 887272
MIN_SQRT_RATIO = 4295128739
MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342

_MAGIC = [
    (0x2, 0xfff97272373d413259a46990580e213a), (0x4, 0xfff2e50f5f656932ef12357cf3c7fdcc),
    (0x8, 0xffe5caca7e10e4e61c3624eaa0941cd0), (0x10, 0xffcb9843d60f6159c9db58835c926644),
    (0x20, 0xff973b41fa98c081472e6896dfb254c0), (0x40, 0xff2ea16466c96a3843ec78b326b52861),
    (0x80, 0xfe5dee046a99a2a811c461f1969c3053), (0x100, 0xfcbe86c7900a88aedcffc83b479aa3a4),
    (0x200, 0xf987a7253ac413176f2b074cf7815e54), (0x400, 0xf3392b0822b70005940c7a398e4b70f3),
    (0x800, 0xe7159475a2c29b7443b29c7fa6e889d9), (0x1000, 0xd097f3bdfd2022b8845ad8f792aa5825),
    (0x2000, 0xa9f746462d870fdf8a65dc1f90e061e5), (0x4000, 0x70d869a156d2a1b890bb3df62baf32f7),
    (0x8000, 0x31be135f97d08fd981231505542fcfa6), (0x10000, 0x9aa508b5b7a84e1c677de54f3e99bc9),
    (0x20000, 0x5d6af8dedb81196699c329225ee604), (0x40000, 0x2216e584f5fa1ea926041bedfe98),
    (0x80000, 0x48a170391f7dc42444e8fa2),
]


def sqrt_at_tick(tick):
    a = abs(tick)
    assert a <= MAX_TICK
    r = 0xfffcb933bd6fad37aa2d162d1a594001 if a & 1 else 1 << 128
    for bit, m in _MAGIC:
        if a & bit:
            r = (r * m) >> 128
    if tick > 0:
        r = (U256 - 1) // r
    return (r >> 32) + (0 if r % (1 << 32) == 0 else 1)


def tick_at_sqrt(sp):
    """Greatest tick with sqrt_at_tick(tick) <= sp (TickMath.getTickAtSqrtRatio)."""
    assert MIN_SQRT_RATIO <= sp < MAX_SQRT_RATIO
    lo, hi = MIN_TICK, MAX_TICK
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if sqrt_at_tick(mid) <= sp:
            lo = mid
        else:
            hi = mid - 1
    return lo


def mul_div(a, b, d):
    return a * b // d


def mul_div_up(a, b, d):
    return -(-a * b // d)


def div_up(a, d):
    return -(-a // d)


def amount0_delta(a, b, L, up):
    if a > b:
        a, b = b, a
    n1, n2 = L << 96, b - a
    return div_up(mul_div_up(n1, n2, b), a) if up else mul_div(n1, n2, b) // a


def amount1_delta(a, b, L, up):
    if a > b:
        a, b = b, a
    return mul_div_up(L, b - a, Q96) if up else mul_div(L, b - a, Q96)


def _next_from_amount0_up(sp, L, amount, add):
    if amount == 0:
        return sp
    n1 = L << 96
    product = amount * sp
    if add:
        if product < U256:  # no overflow in amount * sqrtP
            den = n1 + product
            if den < U256:  # no overflow in n1 + product
                return mul_div_up(n1, sp, den)
        return div_up(n1, n1 // sp + amount)
    assert product < U256 and n1 > product
    return mul_div_up(n1, sp, n1 - product)


def _next_from_amount1_down(sp, L, amount, add):
    if add:
        q = (amount << 96) // L if amount <= U160_MAX else mul_div(amount, Q96, L)
        return sp + q
    q = div_up(amount << 96, L) if amount <= U160_MAX else mul_div_up(amount, Q96, L)
    assert sp > q
    return sp - q


def next_from_input(sp, L, amt, z4o):
    return _next_from_amount0_up(sp, L, amt, True) if z4o else _next_from_amount1_down(sp, L, amt, True)


def next_from_output(sp, L, amt, z4o):
    return _next_from_amount1_down(sp, L, amt, False) if z4o else _next_from_amount0_up(sp, L, amt, False)


def compute_swap_step(cur, target, L, remaining, fee):
    z4o = cur >= target
    exact_in = remaining >= 0
    amount_in = amount_out = 0
    if exact_in:
        less_fee = mul_div(remaining, 1_000_000 - fee, 1_000_000)
        amount_in = amount0_delta(target, cur, L, True) if z4o else amount1_delta(cur, target, L, True)
        nxt = target if less_fee >= amount_in else next_from_input(cur, L, less_fee, z4o)
    else:
        amount_out = amount1_delta(target, cur, L, False) if z4o else amount0_delta(cur, target, L, False)
        nxt = target if -remaining >= amount_out else next_from_output(cur, L, -remaining, z4o)
    mx = target == nxt
    if z4o:
        amount_in = amount_in if mx and exact_in else amount0_delta(nxt, cur, L, True)
        amount_out = amount_out if mx and not exact_in else amount1_delta(nxt, cur, L, False)
    else:
        amount_in = amount_in if mx and exact_in else amount1_delta(cur, nxt, L, True)
        amount_out = amount_out if mx and not exact_in else amount0_delta(cur, nxt, L, False)
    if not exact_in and amount_out > -remaining:
        amount_out = -remaining
    if exact_in and nxt != target:
        fee_amt = remaining - amount_in
    else:
        fee_amt = mul_div_up(amount_in, fee, 1_000_000 - fee)
    return nxt, amount_in, amount_out, fee_amt


class Pool:
    """Pool state: price, active liquidity and initialized ticks (tickSpacing fixed)."""

    def __init__(self, sqrt_price, tick, liquidity, ticks, fee, spacing=1):
        self.sqrt_price, self.tick, self.liquidity = sqrt_price, tick, liquidity
        self.fee, self.spacing = fee, spacing
        self.net = {}    # tick -> liquidityNet
        self.gross = {}  # tick -> liquidityGross
        self.init = []   # sorted initialized ticks
        for t, (gross, net) in ticks.items():
            if gross > 0:
                self.gross[t], self.net[t] = gross, net
        self.init = sorted(self.gross)

    def copy(self):
        p = Pool.__new__(Pool)
        p.sqrt_price, p.tick, p.liquidity, p.fee, p.spacing = (self.sqrt_price, self.tick, self.liquidity,
                                                               self.fee, self.spacing)
        p.net, p.gross, p.init = dict(self.net), dict(self.gross), list(self.init)
        return p

    # -- liquidity events -------------------------------------------------------------------------
    def _update_tick(self, t, d_liq, upper):
        g0 = self.gross.get(t, 0)
        g1 = g0 + d_liq
        if g1 == 0:
            self.gross.pop(t, None)
            self.net.pop(t, None)
            i = bisect.bisect_left(self.init, t)
            if i < len(self.init) and self.init[i] == t:
                self.init.pop(i)
            return
        if g0 == 0:
            bisect.insort(self.init, t)
        self.gross[t] = g1
        self.net[t] = self.net.get(t, 0) + (-d_liq if upper else d_liq)

    def modify(self, lower, upper, d_liq):
        """Mint (d_liq > 0) or burn (d_liq < 0)."""
        if d_liq == 0:
            return
        self._update_tick(lower, d_liq, False)
        self._update_tick(upper, d_liq, True)
        if lower <= self.tick < upper:
            self.liquidity += d_liq

    # -- tick bitmap ------------------------------------------------------------------------------
    def next_tick(self, tick, lte):
        s = self.spacing
        comp = tick // s  # floor division matches the Solidity rounding toward negative infinity
        if lte:
            word = comp >> 8
            lo = word * 256
            i = bisect.bisect_right(self.init, comp * s) - 1
            if i >= 0 and self.init[i] // s >= lo:
                return self.init[i], True
            return lo * s, False
        comp += 1
        word = comp >> 8
        hi = word * 256 + 255
        i = bisect.bisect_left(self.init, comp * s)
        if i < len(self.init) and self.init[i] // s <= hi:
            return self.init[i], True
        return hi * s, False

    # -- swap -------------------------------------------------------------------------------------
    def swap(self, z4o, amount_specified, limit=None):
        """Mutates state. Returns (amount0, amount1) from the pool's view (positive = paid in)."""
        if limit is None:
            limit = MIN_SQRT_RATIO + 1 if z4o else MAX_SQRT_RATIO - 1
        assert amount_specified != 0
        if z4o:
            assert MIN_SQRT_RATIO < limit < self.sqrt_price
        else:
            assert self.sqrt_price < limit < MAX_SQRT_RATIO
        exact_in = amount_specified > 0
        rem, calc = amount_specified, 0
        sp, tick, L = self.sqrt_price, self.tick, self.liquidity
        while rem != 0 and sp != limit:
            start = sp
            nt, inited = self.next_tick(tick, z4o)
            nt = max(MIN_TICK, min(MAX_TICK, nt))
            sp_next = sqrt_at_tick(nt)
            target = limit if (sp_next < limit if z4o else sp_next > limit) else sp_next
            sp, a_in, a_out, fee_amt = compute_swap_step(sp, target, L, rem, self.fee)
            if exact_in:
                rem -= a_in + fee_amt
                calc -= a_out
            else:
                rem += a_out
                calc += a_in + fee_amt
            if sp == sp_next:
                if inited:
                    net = self.net[nt]
                    L += -net if z4o else net
                tick = nt - 1 if z4o else nt
            elif sp != start:
                tick = tick_at_sqrt(sp)
        self.sqrt_price, self.tick, self.liquidity = sp, tick, L
        if z4o == exact_in:
            return amount_specified - rem, calc
        return calc, amount_specified - rem

    def state(self):
        return self.sqrt_price, self.tick, self.liquidity

    def set_state(self, st):
        self.sqrt_price, self.tick, self.liquidity = st

    def quote(self, z4o, amount_specified, limit=None):
        """Swap without changing state. Swaps never change tick data, so restoring three fields suffices."""
        st = self.state()
        try:
            return self.swap(z4o, amount_specified, limit)
        finally:
            self.set_state(st)
