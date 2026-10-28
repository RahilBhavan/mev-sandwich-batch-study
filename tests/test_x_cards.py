"""The two X cards' numbers are the repo's results, not new ones."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import x_cards  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def summary():
    return json.load(open(os.path.join(RESULTS, "summary.json")))


def test_replay_card_matches_summary():
    s, spec = summary(), x_cards.replay_spec(summary())
    assert spec["marker"]["text"] == "52%" and spec["marker"]["at"] == 51.72 == 100 * s["prevented_share_static_arrival"]
    assert spec["band"]["label"] == "200 random: mean 75%"
    assert spec["band"]["text"] == "5th–95th: 68–84%"
    assert (spec["band"]["from"], spec["band"]["to"]) == (67.84, 84.03)
    assert spec["axis"] == "Loss recovered, of $12,387" and s["draws"] == 200


def test_slippage_card_matches_victims_and_summary():
    s = summary()
    n, slack, taken = x_cards.tolerance(RESULTS)
    spec = x_cards.slippage_spec(s, n, slack, taken)
    assert (n, s["victims"]) == (115, 244) == (s["victims_with_slack_c"], s["victims"])
    assert abs(slack - s["slippage_slack_c_usd"]) < 0.01
    assert spec["title"] == "98% of the tolerance, taken."
    assert spec["axis"] == "Of $1,582, 115 of 244 victims"
    assert (spec["taken"]["text"], spec["left"]["text"]) == ("$1,544", "$38")


def test_committed_specs_and_alt_are_current():
    for spec in x_cards.specs(RESULTS):
        d = os.path.join(RESULTS, "x-cards", spec["id"])
        assert json.load(open(os.path.join(d, "spec.json"))) == spec
        assert open(os.path.join(d, "alt.txt")).read().strip() == spec["alt"]
        assert len(spec["alt"]) <= 1000
        assert "github.com/RahilBhavan/mev-sandwich-batch-study" in spec["alt"]
