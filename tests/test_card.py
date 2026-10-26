"""The get-back card's numbers are the repo's results, not new ones."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import card  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_card_shares_match_summary():
    loss, rows = card.scenarios(os.path.join(ROOT, "results"))
    s = json.load(open(os.path.join(ROOT, "results", "summary.json")))
    assert abs(loss - s["loss_a_usd"]) < 0.01
    want = [s["prevented_share_static_arrival"], s["prevented_share_static_random_mean"],
            s["prevented_share_static_attacker_unlimited_arrival"], s["prevented_share_deterred"]]
    assert [round(r["share"], 4) for r in rows] == want


def test_attacker_series_label_is_exact():
    assert card.ATTACKER_LABEL == "Attacker, no slippage limit (arrival)"
    assert card.SCENARIOS[2][0] == card.ATTACKER_LABEL
