"""The Wed Oct 28 X cards carry the requested text verbatim and numbers that come from the results files."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import x_cards  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SUMMARY = json.load(open(os.path.join(RESULTS, "summary.json")))
REPLAY, SLIPPAGE = x_cards.specs(RESULTS)


def test_replay_text_is_verbatim():
    assert REPLAY["title"] == "Replay recovered 75%. Arrival order: 52%."
    assert REPLAY["axis"] == "Share of $12,387 sandwich loss recovered (counterfactual replay)"
    assert REPLAY["source"] == "Source: mev-sandwich-batch-study replay · busiest WETH/USDT pool, Oct 5–11, 2026"


def test_slippage_text_is_verbatim():
    assert SLIPPAGE["axis"] == ("Slippage tolerance (no-attack output − victim's minimum), "
                                "115 of 244 victims with decoded nonzero limits")
    assert SLIPPAGE["source"] == "Source: mev-sandwich-batch-study methods.md · busiest WETH/USDT pool, Oct 5–11, 2026"


def test_replay_numbers_match_summary():
    assert REPLAY["arrival"] == 100 * SUMMARY["prevented_share_static_arrival"]
    assert REPLAY["mean"] == 100 * SUMMARY["prevented_share_static_random_mean"]
    assert REPLAY["band"] == [100 * SUMMARY["prevented_share_static_random_p5"], 100 * SUMMARY["prevented_share_static_random_p95"]]
    assert REPLAY["band_text"] == "Random orders: 68–84%, mean 75%"
    assert REPLAY["arrival_text"] == "52%"


def test_slippage_numbers_match_summary():
    n, slack, taken = x_cards.tolerance(RESULTS)
    assert n == SUMMARY["victims_with_slack_c"] == 115
    assert abs(slack - SUMMARY["slippage_slack_c_usd"]) < 0.01
    assert (SLIPPAGE["taken_text"], SLIPPAGE["left_text"]) == ("Taken $1,544", "Left $38")
    assert SLIPPAGE["title"] == "98% of the tolerance, taken."


def test_alt_text_carries_every_printed_number():
    for spec, printed in ((REPLAY, ("75%", "52%", "68–84%", "$12,387", "200", "Oct 5–11, 2026")),
                          (SLIPPAGE, ("98%", "115 of 244", "$1,582", "$1,544", "$38", "Oct 5–11, 2026"))):
        for p in printed:
            assert p in spec["alt"], (spec["id"], p)
