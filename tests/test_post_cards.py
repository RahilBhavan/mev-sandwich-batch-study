"""The Oct 28 post cards print the study's numbers and the wording Rahil asked for. No browser needed."""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import post_cards  # noqa: E402

OUT = os.path.join(ROOT, "results", "post-cards")
N = post_cards.numbers(os.path.join(ROOT, "results"))
CARDS = {c["id"]: c for c in post_cards.cards(N)}


def shown(card):
    return " ".join([card["title"], card["context"], card["note"], *card["foot"],
                     *[f"{label} {value}" for label, value, _ in card["rows"]]]).replace("|", " ")


def test_numbers_match_the_kit():
    mev = shown(CARDS["wed28-am-mev"])
    for text in ("51.7%", "75.4%", "68%–84%", "$12,387", "mean of 200", "5th–95th"):
        assert text in mev, text
    slip = shown(CARDS["wed28-pm-mev-slippage"])
    for text in ("$1,582", "$1,544", "98%", "115 of 244", "not a median"):
        assert text in slip, text


def test_mev_card_wording():
    mev = shown(CARDS["wed28-am-mev"])
    assert "Random mean" not in mev and "Random mean" not in CARDS["wed28-am-mev"]["alt"]
    assert "Random tie-breaks" in mev and "WETH/USDT" in mev and "Oct 5–11, 2026" in mev and "Same orders" in mev
    for line in CARDS["wed28-am-mev"]["foot"] + [CARDS["wed28-am-mev"]["note"]]:
        assert line.strip().lower() not in ("replay", "replay.", "replay,")


def test_every_card_has_a_source_and_date_footer():
    for card in CARDS.values():
        assert any(line.startswith("Source: ") for line in card["foot"])
        assert any("Oct 17, 2026" in line for line in card["foot"])


def test_alt_text_is_one_paragraph_that_starts_from_the_title():
    for card in CARDS.values():
        alt = card["alt"]
        assert "\n" not in alt and "  " not in alt and alt == alt.strip()
        assert alt.startswith(card["title"].replace("|", " ")), alt
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
