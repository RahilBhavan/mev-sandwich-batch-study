"""The Oct 28 post cards print the study's numbers and the reviewed wording. No browser needed."""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import post_cards  # noqa: E402

OUT = os.path.join(ROOT, "results", "post-cards")
N = post_cards.numbers(os.path.join(ROOT, "results"))
CARDS = {c["id"]: c for c in post_cards.cards(N)}


def shown(card):
    """The text a reader sees: the card's HTML body with tags removed (the chart's bar positions are not text)."""
    body = post_cards.card_html(card).split("<body>")[1]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body.replace("<br>", " "))).replace("  ", " ")


def test_numbers_match_the_study():
    mev = shown(CARDS["wed28-am-mev"])
    for text in ("Replay recovered 75%. Arrival order: 52%.", "$12,387", "Random: 68–84%", "mean 75%", "0%", "100%", "counterfactual replay"):
        assert text in mev, text
    assert (round(N["arrival"], 3), round(N["mean"], 3)) == (0.517, 0.754)
    assert (round(N["p5"], 2), round(N["p95"], 2)) == (0.68, 0.84)
    slip = shown(CARDS["wed28-pm-mev-slippage"])
    for text in ("$1,582", "$1,544", "98%", "115 of 244", "decoded nonzero limits"):
        assert text in slip, text


def test_panel_labels_and_footers_are_the_reviewed_wording():
    assert CARDS["wed28-am-mev"]["context"] == "Share of $12,387 sandwich loss recovered (counterfactual replay)"
    assert CARDS["wed28-am-mev"]["foot"] == "Source: mev-sandwich-batch-study replay · busiest WETH/USDT pool, Oct 5–11, 2026"
    assert CARDS["wed28-pm-mev-slippage"]["context"] == (
        "Slippage tolerance (no-attack output − victim's minimum), 115 of 244 victims with decoded nonzero limits")
    assert CARDS["wed28-pm-mev-slippage"]["foot"] == (
        "Source: mev-sandwich-batch-study methods.md · busiest WETH/USDT pool, Oct 5–11, 2026")


def test_mev_chart_marks_the_mean_on_the_random_orders_bar_and_labels_zero():
    html = post_cards.card_html(CARDS["wed28-am-mev"])
    assert 'class="mean"' in html and f"left:{post_cards.pc(N['mean'])}" in html
    assert f"left:{post_cards.pc(N['p5'])};width:{post_cards.pc(N['p95'] - N['p5'])}" in html
    assert ">0%</span>" in html and ">100%</span>" in html


def test_alt_text_is_one_paragraph_that_starts_from_the_title():
    for card in CARDS.values():
        alt = card["alt"]
        assert "\n" not in alt and "  " not in alt and alt == alt.strip()
        assert alt.startswith(card["title"].replace("|", " ")), alt
        assert card["context"] in alt and card["foot"].split(" · ")[0] in alt and "busiest WETH/USDT pool, Oct 5–11, 2026" in alt, alt
        committed = open(os.path.join(OUT, f"{card['id']}.alt.txt")).read()
        assert committed == alt + "\n"


def test_committed_pngs_match_the_hash_list():
    sums = dict(reversed(line.split("  ")) for line in open(os.path.join(OUT, "SHA256SUMS")).read().split("\n") if line)
    assert sorted(sums) == sorted(f"{i}-square.png" for i in CARDS)
    for name, sha in sums.items():
        assert hashlib.sha256(open(os.path.join(OUT, name), "rb").read()).hexdigest() == sha


def test_palette_check_passes_for_both_pngs():
    for card_id in CARDS:
        report = post_cards.palette_report(os.path.join(OUT, f"{card_id}-square.png"))
        assert report["size"] == (1080, 1080) and report["off_palette"] == 0
