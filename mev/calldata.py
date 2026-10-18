"""Decode swap limits from router calldata for swaps on the study pool.

Supported: Uniswap Universal Router execute() (V3_SWAP_EXACT_IN / V3_SWAP_EXACT_OUT), SwapRouter02 and
SwapRouter (v1), including multicall. Returns one record per decoded single-hop swap through the study pool:
  dict(exact_in, amount, bound, sqrt_limit, multihop=False)
where amount is the specified amount, bound is amountOutMinimum (exact in) or amountInMaximum (exact out).
Multi-hop paths through the pool are returned with multihop=True: their bound covers the whole path,
so it cannot be attributed to this pool's hop.
"""
WETH = "c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDT = "dac17f958d2ee523a2206206994597c13d831ec7"
FEE = 100
CONTRACT_BALANCE = 1 << 255

UR_EXEC = ("3593564c", "24856bc3")  # execute(bytes,bytes[],uint256), execute(bytes,bytes[])
MULTICALL = ("5ae401dc", "ac9650d8", "1f0464d1")


def _w(b, i):
    return int.from_bytes(b[i:i + 32], "big")


def _bytes_at(b, off):
    n = _w(b, off)
    return b[off + 32:off + 32 + n]


def _array_of_bytes(b, off):
    n = _w(b, off)
    base = off + 32
    return [_bytes_at(b, base + _w(b, base + 32 * k)) for k in range(n)]


def _path(p):
    """Parse a v3 path into hops [(tokenA, fee, tokenB)] as lowercase hex without 0x."""
    hops = []
    i = 0
    while i + 43 <= len(p):
        a = p[i:i + 20].hex()
        fee = int.from_bytes(p[i + 20:i + 23], "big")
        b = p[i + 23:i + 43].hex()
        hops.append((a, fee, b))
        i += 23
    return hops


def _is_pool(a, fee, b):
    return fee == FEE and {a, b} == {WETH, USDT}


def _from_path(path, exact_in, amount, bound):
    hops = _path(path)
    mine = [h for h in hops if _is_pool(*h)]
    if not mine:
        return []
    return [dict(exact_in=exact_in, amount=amount, bound=bound, sqrt_limit=0, multihop=len(hops) > 1)]


def _single(tin, tout, fee, exact_in, amount, bound, sqrt_limit):
    if not _is_pool(tin, fee, tout):
        return []
    return [dict(exact_in=exact_in, amount=amount, bound=bound, sqrt_limit=sqrt_limit, multihop=False)]


def _router_call(c):
    sel, a = c[:4].hex(), c[4:]
    addr = lambda i: a[i + 12:i + 32].hex()
    if sel == "04e45aaf":  # SR02 exactInputSingle(tokenIn,tokenOut,fee,recipient,amountIn,amountOutMin,sqrtLimit)
        return _single(addr(0), addr(32), _w(a, 64), True, _w(a, 128), _w(a, 160), _w(a, 192))
    if sel == "5023b4df":  # SR02 exactOutputSingle(..., amountOut, amountInMax, sqrtLimit)
        return _single(addr(0), addr(32), _w(a, 64), False, _w(a, 128), _w(a, 160), _w(a, 192))
    if sel == "414bf389":  # SR exactInputSingle(tokenIn,tokenOut,fee,recipient,deadline,amountIn,amountOutMin,sqrtLimit)
        return _single(addr(0), addr(32), _w(a, 64), True, _w(a, 160), _w(a, 192), _w(a, 224))
    if sel == "db3e2198":
        return _single(addr(0), addr(32), _w(a, 64), False, _w(a, 160), _w(a, 192), _w(a, 224))
    if sel in ("b858183f", "09b81346"):  # SR02 exactInput/exactOutput((path,recipient,amount,bound))
        s = _w(a, 0)
        return _from_path(_bytes_at(a, s + _w(a, s)), sel == "b858183f", _w(a, s + 64), _w(a, s + 96))
    if sel in ("c04b8d59", "f28c0498"):  # SR exactInput/exactOutput((path,recipient,deadline,amount,bound))
        s = _w(a, 0)
        return _from_path(_bytes_at(a, s + _w(a, s)), sel == "c04b8d59", _w(a, s + 96), _w(a, s + 128))
    if sel in MULTICALL:
        off = _w(a, 32) if sel in ("5ae401dc", "1f0464d1") else _w(a, 0)
        out = []
        for inner in _array_of_bytes(a, off):
            out += _router_call(inner)
        return out
    return []


def _universal(c):
    a = c[4:]
    cmds = _bytes_at(a, _w(a, 0))
    inputs = _array_of_bytes(a, _w(a, 32))
    out = []
    for cmd, inp in zip(cmds, inputs):
        t = cmd & 0x3f
        if t in (0x00, 0x01):  # V3_SWAP_EXACT_IN / OUT: (recipient, amount, bound, path, payerIsUser)
            path = _bytes_at(inp, _w(inp, 96))
            amount = _w(inp, 32)
            out += _from_path(path, t == 0x00, None if amount == CONTRACT_BALANCE else amount, _w(inp, 64))
    return out


def decode(input_hex):
    try:
        c = bytes.fromhex(input_hex[2:])
        if len(c) < 4:
            return []
        if c[:4].hex() in UR_EXEC:
            return _universal(c)
        return _router_call(c)
    except (IndexError, ValueError):
        return []


# -- route-level bounds from aggregators and smart-wallet wrappers ------------------------------------
# An aggregator's minimum output covers its whole route. It is a limit for this pool only when the route is this
# pool alone; the caller must check that from the receipt. Every decode is validated against the logs: the
# specified input must equal the swap's actual input (up to a 1% aggregator fee) and the bound must not exceed the actual output.
SEL_1INCH_SWAP = "07ed2379"     # 1inch v6 swap(executor, (src,dst,srcRecv,dstRecv,amount,minReturn,flags), data)
SEL_KYBER_SWAP = "e21fd0e9"     # KyberSwap MetaAggregationRouterV2 swap(SwapExecutionParams)
ADJACENT_SELS = ("0d5f0e3b", "0c307f76")  # router 0x8feab81d (2,296 senders that week): amount then minReturn
SEL_ALLOWANCE_EXEC = "2213bc0b"  # 0x AllowanceHolder exec(operator, token, amount, target, data)
SEL_SETTLER_EXEC = "1fff991f"   # 0x Settler execute((recipient, buyToken, minAmountOut), actions, bytes32)
LIFI_SWAPS = ("736eac0b", "80c65808", "17917a4e", "a3443faa", "4630a0d8", "5fd9ae2e", "2c57e884")
# LI.FI swap facets: (bytes32 txId, string integrator, string referrer, address receiver, uint256 minAmountOut, ...)
ROUTER_SELS = {bytes.fromhex(s) for s in UR_EXEC + MULTICALL + ("04e45aaf", "5023b4df", "414bf389", "db3e2198",
                                                                    "b858183f", "09b81346", "c04b8d59", "f28c0498")}


def _words(b):
    return [_w(b, i) for i in range(0, len(b) - 31, 32)]


def _amount_ok(x, paid):
    """The router's specified input may exceed what reached the pool by an aggregator fee of up to 1%."""
    return paid <= x <= paid * 101 // 100


def _adjacent(a, paid, got):
    """amount followed by minReturn (1inch and KyberSwap swap descriptions)."""
    ws = _words(a)
    for i in range(len(ws) - 1):
        if _amount_ok(ws[i], paid) and 0 < ws[i + 1] <= got and ws[i + 1] * 2 >= got:
            return ws[i + 1]
    return None


def _route_bound(c, paid, got, out_token):
    sel, a = c[:4].hex(), c[4:]
    if sel == SEL_1INCH_SWAP and len(a) >= 224:
        # swap(executor, (srcToken, dstToken, srcReceiver, dstReceiver, amount, minReturnAmount, flags), data):
        # the struct is static, so its fields sit at fixed head words; validate the destination token
        dst, m = a[64 + 12:96].hex(), _w(a, 192)
        ok_token = dst == out_token or (out_token == WETH and dst == "e" * 40)
        if ok_token and 0 < m <= got and m * 2 >= got:
            return m
        return _adjacent(a, paid, got)
    if sel in (SEL_KYBER_SWAP,) + ADJACENT_SELS:
        return _adjacent(a, paid, got)
    if sel in LIFI_SWAPS and len(a) >= 160:
        m = _w(a, 128)
        return m if 0 < m <= got and m * 2 >= got else None
    if sel == SEL_ALLOWANCE_EXEC and _amount_ok(_w(a, 64), paid):
        inner = _bytes_at(a, _w(a, 128))
        return _route_bound(inner, paid, got, out_token)
    if sel == SEL_SETTLER_EXEC:
        buy, m = a[44:64].hex(), _w(a, 64)
        ok_token = buy == out_token or (out_token == WETH and buy == "e" * 40)
        return m if ok_token and 0 < m <= got and m * 2 >= got else None
    return None


def decode_embedded(input_hex):
    """Router calls nested in smart-wallet or relayer calldata: decode from each embedded router selector."""
    c = bytes.fromhex(input_hex[2:])
    out = []
    for sel in ROUTER_SELS:
        i = c.find(sel, 4)
        while i != -1:
            try:
                out = decode("0x" + c[i:].hex())
            except Exception:
                out = []
            if out:
                return out
            i = c.find(sel, i + 1)
    return out


def route_bound(input_hex, paid, got, z4o):
    """Minimum output for an exact-input route, from an aggregator call at the top level or embedded."""
    out_token = USDT if z4o else WETH
    try:
        c = bytes.fromhex(input_hex[2:])
    except ValueError:
        return None
    m = _route_bound(c, paid, got, out_token)
    if m is not None:
        return m
    for s in (SEL_1INCH_SWAP, SEL_KYBER_SWAP, SEL_ALLOWANCE_EXEC, SEL_SETTLER_EXEC) + LIFI_SWAPS:
        i = c.find(bytes.fromhex(s), 4)
        if i != -1:
            m = _route_bound(c[i:], paid, got, out_token)
            if m is not None:
                return m
    return None
