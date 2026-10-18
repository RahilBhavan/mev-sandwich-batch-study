import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mev import detect


def sw(tx, li, a0, a1):
    return dict(tx=tx, log_index=li, amount0=a0, amount1=a1, block=1)


META = {"F": ("0xatk", "0xbot"), "V": ("0xuser", "0xrouter"), "B": ("0xatk", "0xbot"),
        "V2": ("0xuser2", "0xrouter"), "X": ("0xother", "0xrouter"), "B2": ("0xatk2", "0xbot")}


def test_basic_sandwich():
    s = [sw("F", 1, -10, 100), sw("V", 2, -5, 50), sw("B", 3, 10, -101)]
    r = detect.detect_block(1, s, META)
    assert len(r) == 1 and r[0]["victims"] == ["V"] and r[0]["strict"]


def test_burger_two_victims_and_other_direction_ignored():
    s = [sw("F", 1, -10, 100), sw("V", 2, -5, 50), sw("X", 3, 3, -30), sw("V2", 4, -1, 10), sw("B", 5, 10, -100)]
    r = detect.detect_block(1, s, META)
    assert r[0]["victims"] == ["V", "V2"]


def test_amount_mismatch_rejected():
    s = [sw("F", 1, -10, 100), sw("V", 2, -5, 50), sw("B", 3, 5, -60)]  # sells back 60 of 100
    assert detect.detect_block(1, s, META) == []


def test_same_bot_contract_needs_tight_match():
    s = [sw("F", 1, -100, 1000), sw("V", 2, -5, 50), sw("B2", 3, 105, -1000)]  # sells back 105% of what F bought
    assert detect.detect_block(1, s, META) == []
    s[2] = sw("B2", 3, 100, -1000)
    assert len(detect.detect_block(1, s, META)) == 1


def test_no_victim_no_sandwich():
    s = [sw("F", 1, -10, 100), sw("X", 2, 3, -30), sw("B", 3, 10, -100)]
    assert detect.detect_block(1, s, META) == []
