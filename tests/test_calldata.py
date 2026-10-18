import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import calldata

W = lambda v: v.to_bytes(32, "big")
A = lambda h: bytes(12) + bytes.fromhex(h)


def test_sr02_exact_input_single():
    c = bytes.fromhex("04e45aaf") + A(calldata.T0) + A(calldata.T1) + W(100) + A("11" * 20) + W(10**18) + W(2500 * 10**6) + W(0)
    d = calldata.decode("0x" + c.hex())
    assert d == [dict(exact_in=True, amount=10**18, bound=2500 * 10**6, sqrt_limit=0, multihop=False)]


def test_other_pool_ignored():
    c = bytes.fromhex("04e45aaf") + A(calldata.T0) + A(calldata.T1) + W(500) + A("11" * 20) + W(1) + W(1) + W(0)
    assert calldata.decode("0x" + c.hex()) == []


def test_embedded_router_call_in_wallet_batch():
    inner = bytes.fromhex("04e45aaf") + A(calldata.T0) + A(calldata.T1) + W(100) + A("11" * 20) + W(5) + W(4) + W(0)
    wrapper = bytes.fromhex("34fcd5be") + W(32) + W(len(inner)) + inner
    assert calldata.decode_embedded("0x" + wrapper.hex())[0]["bound"] == 4


def test_1inch_slots_and_fee_tolerance():
    paid, got = 10**18, 2500 * 10**6
    c = (bytes.fromhex(calldata.SEL_1INCH_SWAP) + A("22" * 20) + A(calldata.T0) + A(calldata.T1) + A("33" * 20)
         + A("44" * 20) + W(paid + paid // 200) + W(2490 * 10**6) + W(0) + W(288) + W(0))
    assert calldata.route_bound("0x" + c.hex(), paid, got, True) == 2490 * 10**6
    # a bound above the actual output is rejected (the swap would have reverted)
    assert calldata.route_bound("0x" + c.hex(), paid, 2400 * 10**6, True) is None


def test_adjacent_rejects_amount_outside_fee_tolerance():
    paid, got = 1000, 900
    c = bytes.fromhex(calldata.SEL_KYBER_SWAP) + W(paid * 2) + W(890)
    assert calldata.route_bound("0x" + c.hex(), paid, got, True) is None
    c = bytes.fromhex(calldata.SEL_KYBER_SWAP) + W(paid) + W(890)
    assert calldata.route_bound("0x" + c.hex(), paid, got, True) == 890
