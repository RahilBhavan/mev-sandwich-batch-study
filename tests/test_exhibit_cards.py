"""The Oct 28 exhibit cards show the repo's results, are 1080x1080 and keep their wording."""
import json
import os
import re
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "results", "cards")
load = lambda name: json.load(open(os.path.join(CARDS, f"{name}.exhibit.json")))


def png_size(name):
    head = open(os.path.join(CARDS, f"{name}.png"), "rb").read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", head[16:24])


def test_sandwich_card_numbers_are_the_summary_numbers():
    s = json.load(open(os.path.join(ROOT, "results", "summary.json")))
    rows = {r["label"]: r for r in load("wed28-am-mev")["params"]["rows"]}
    arrival, spread = rows["Arrival order"], rows["Random orders"]
    assert round(arrival["at"], 2) == round(100 * s["prevented_share_static_arrival"], 2)
    assert round(spread["mean"], 2) == round(100 * s["prevented_share_static_random_mean"], 2)
    assert round(spread["from"], 2) == round(100 * s["prevented_share_static_random_p5"], 2)
    assert round(spread["to"], 2) == round(100 * s["prevented_share_static_random_p95"], 2)
    assert (arrival["text"], spread["mean_text"], spread["text"]) == ("52%", "Mean 75%", "68–84%")
    assert f"${s['loss_a_usd']:,.0f}" == "$12,387" and "$12,387" in load("wed28-am-mev")["sub"]


def test_slippage_card_numbers_are_the_tables_numbers():
    tables = open(os.path.join(ROOT, "results", "tables.md")).read()
    spec = load("wed28-pm-mev-slippage")
    for text in ("$1,582", "$1,544", "(98%)", "115 victims"):
        assert text in tables
    assert [r[2] for r in spec["params"]["rows"]] == ["$1,544", "$38"]
    assert spec["hero"][0] == "98%" and "115 of 244 victims" in spec["sub"]
    assert round(1544 / 1582 * 100) == 98 and 1582 - 1544 == 38


def test_cards_are_square_1080_and_use_the_requested_wording():
    for name in ("wed28-am-mev", "wed28-pm-mev-slippage"):
        assert png_size(name) == (1080, 1080)
        spec = load(name)
        assert spec["foot_ink"] == "ink"  # footer text in #F5F5EF
        assert spec["source"].endswith("busiest WETH/USDT pool, Oct 5–11, 2026")
        assert not re.search(r"uniform-price", json.dumps(spec), re.I)
    assert load("wed28-am-mev")["title"] == "Replay recovered 75%. Arrival order: 52%."
    assert load("wed28-am-mev")["sub"] == "Share of $12,387 sandwich loss recovered (counterfactual replay)"
    assert load("wed28-pm-mev-slippage")["sub"] == ("Slippage tolerance (no-attack output − victim's minimum), "
                                                    "115 of 244 victims with decoded nonzero limits")
