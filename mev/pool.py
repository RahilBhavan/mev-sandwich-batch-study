"""Constants for the study pools and event decoding.

The environment variable STUDY_POOL selects the pool (default: the main study pool, weth-usdt).
"""
import os

CONFIGS = {
    # main study pool
    "weth-usdt": dict(pool="0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b", name="WETH/USDT 0.01%",
                      token0=("WETH", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 18),
                      token1=("USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7", 6), fee=100, spacing=1),
    # memecoin extension: the most-sandwiched v3 pool on 2026-10-07 (scripts/probe_all_pools.py)
    "simd-weth": dict(pool="0x7c0cfa93c65733bf2034900fdc672673c4fa4e71", name="SIMD/WETH 0.01%",
                      token0=("SIMD", "0xb6026518463ec80f1cb33e4318e802487c27f995", 18),
                      token1=("WETH", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 18), fee=100, spacing=1),
}
KEY = os.environ.get("STUDY_POOL", "weth-usdt")
CFG = CONFIGS[KEY]
POOL, NAME = CFG["pool"], CFG["name"]
(TOKEN0, TOKEN0_ADDR, DEC0), (TOKEN1, TOKEN1_ADDR, DEC1) = CFG["token0"], CFG["token1"]
FEE_PIPS = CFG["fee"]
TICK_SPACING = CFG["spacing"]
WETH_ADDR = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
WEEK = (26122440, 26172657)  # 2026-10-05 00:00:00 .. 2026-10-11 23:59:59 UTC

T_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
T_MINT = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
T_BURN = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
T_COLLECT = "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"
T_FLASH = "0xbdbdb71d7860376ba52b25a5028beea23581364a40522f6bcfb86bb1f2dca633"


def s256(h):
    v = int(h, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def words(data):
    return [data[2 + i:2 + i + 64] for i in range(0, len(data) - 2, 64)]


def decode(lg):
    """Return a dict for Swap/Mint/Burn logs, None for others."""
    t = lg["topics"][0]
    base = dict(block=int(lg["blockNumber"], 16), tx_index=int(lg["transactionIndex"], 16),
                log_index=int(lg["logIndex"], 16), tx=lg["transactionHash"])
    w = words(lg["data"])
    if t == T_SWAP:
        return dict(base, kind="swap", sender="0x" + lg["topics"][1][-40:], recipient="0x" + lg["topics"][2][-40:],
                    amount0=s256(w[0]), amount1=s256(w[1]), sqrtPriceX96=int(w[2], 16),
                    liquidity=int(w[3], 16), tick=s256(w[4]))
    if t in (T_MINT, T_BURN):
        lower, upper = s256(lg["topics"][2]), s256(lg["topics"][3])
        if t == T_MINT:  # sender, amount, amount0, amount1
            amt, a0, a1 = int(w[1], 16), int(w[2], 16), int(w[3], 16)
        else:            # amount, amount0, amount1
            amt, a0, a1 = int(w[0], 16), int(w[1], 16), int(w[2], 16)
        return dict(base, kind="mint" if t == T_MINT else "burn", owner="0x" + lg["topics"][1][-40:],
                    tick_lower=lower, tick_upper=upper, liq_amount=amt, amount0=a0, amount1=a1)
    return None
