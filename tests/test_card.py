"""The cards' numbers are the repo's results, not new ones, and the committed PNGs match their hash manifest."""
import hashlib
import json
import os
import re
import sys

from PIL import Image  # installed with matplotlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import card  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SUMMARY = json.load(open(os.path.join(RESULTS, "summary.json")))


def test_card_shares_match_summary():
    loss, rows = card.scenarios(RESULTS)
    assert abs(loss - SUMMARY["loss_a_usd"]) < 0.01
    assert [round(r["share"], 4) for r in rows] == [SUMMARY[key] for _, _, key, _ in card.SCENARIOS]


def test_mev_card_has_five_rows_and_one_red_row():
    rows = card.mev_card(RESULTS, square=False)["rows"]
    assert [r["label"] for r in rows] == [
        "Same orders, arrival order",
        "Same orders, random tie-break (mean of 200): p5-p95 68-84%",
        "Attacker, no slippage limit (arrival)",
        "Every order, no slippage limits (arrival)",
        "If attackers stay out: about 100%",
    ]
    assert [r["accent"] for r in rows] == [False, True, False, False, False]
    assert [r["bar"].split(" · ")[-1] for r in rows[:4]] == ["52%", "75%", "87%", "88%"]


def test_mev_card_wording():
    spec = card.mev_card(RESULTS, square=False)
    assert spec["title"][1].startswith("about 75%") and "75%" in " ".join(spec["title"])
    assert spec["sub"] == ["No sandwich made money under batch clearing."]
    assert spec["axis"] == "Share of the $12,387 loss victims get back"
    text = json.dumps(spec)
    assert "keep" not in text and ">99%" not in text and "99.99%" not in text


def test_slippage_card_uses_the_readme_count():
    n, tolerance, taken = card.slippage(RESULTS)
    assert n == SUMMARY["victims_with_slack_c"] == 115
    assert round(tolerance) == 1582 and round(taken) == 1544 and f"{taken / tolerance:.0%}" == "98%"
    spec = card.slippage_card(RESULTS, square=True)
    shown = [*spec["title"], *spec["sub"], *spec["foot"], spec["axis"]] + [r[k] for r in spec["rows"] for k in ("label", "bar", "alt")]
    assert not re.search(r"\b144\b", " ".join(shown))


def test_alt_text_lists_every_drawn_row():
    for name, build in card.CARDS.items():
        spec = build(RESULTS, square=True)
        alt = card.alt_text(name, spec)
        assert [r["frac"] for r in spec["rows"]] == [r["frac"] for r in build(RESULTS, square=False)["rows"]]
        for r in spec["rows"]:
            assert r["alt"] in alt


def test_committed_pngs_match_manifest_and_sizes():
    lines = [x.split("  ") for x in open(os.path.join(RESULTS, "cards.sha256")).read().split("\n") if x]
    assert sorted(n for _, n in lines) == sorted(f"{c}-{s}.png" for c in card.CARDS for s in card.SIZES)
    for digest, name in lines:
        path = os.path.join(RESULTS, name)
        assert hashlib.sha256(open(path, "rb").read()).hexdigest() == digest, name
        assert Image.open(path).size == (card.W, card.SIZES[name.rsplit("-", 1)[1][:-4]]), name
