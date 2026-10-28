# Wed Oct 28 X cards: Chart Reviewer fixes (request cr-7fde98d2)

Two 1080×1080 cards for the Oct 28 posts, rebuilt with Chart Reviewer's exact fixes. Post text is unchanged.
**Design review pending.** These are review drafts: no named reviewer has passed these exact bytes, and the
`wed28-am-mev` labels are below the feed floor (see Checks).

| Card | Folder | Alt text |
| --- | --- | --- |
| Replay | `wed28-am-mev/` | `wed28-am-mev/alt.txt` |
| Slippage tolerance | `wed28-pm-mev-slippage/` | `wed28-pm-mev-slippage/alt.txt` |

Each folder holds `card.png` (the 1080×1080 export), `card.html` (self-contained source), `alt.txt`, `brief.json` (measurements)
and `spec.json` (the text and numbers drawn). Rebuild with
`uv run --with playwright==1.63.0 python scripts/x_cards.py --render`; the render is byte-for-byte repeatable.

## Fixes applied

Replay (`wed28-am-mev`): 1080×1080; the 75% random-tie-break mean is a dark tick on the random-orders bar, labelled
"mean 75%"; title `Replay recovered 75%. Arrival order: 52%.`; `0%` at the left end of the axis; panel label
`Share of $12,387 sandwich loss recovered (counterfactual replay)`; footer
`Source: mev-sandwich-batch-study replay · busiest WETH/USDT pool, Oct 5–11, 2026` in #F5F5EF; alt text updated.

Slippage (`wed28-pm-mev-slippage`): 1080×1080; panel label
`Slippage tolerance (no-attack output − victim's minimum), 115 of 244 victims with decoded nonzero limits`; footer
`Source: mev-sandwich-batch-study methods.md · busiest WETH/USDT pool, Oct 5–11, 2026` in #F5F5EF; alt text updated.

## Numbers

All from `results/summary.json` and `results/victims.csv`; none typed by hand (`tests/test_x_cards.py` checks them).
Arrival 51.72% → 52%; random mean 75.45% → 75%; random 5th–95th 67.84–84.03% → 68–84%; loss $12,386.84 → $12,387;
115 of 244 victims; tolerance $1,581.69 → $1,582 (matches `slippage_slack_c_usd`). Taken $1,543.96 → $1,544 and left $37.73
→ $38 are not in `summary.json`; they are summed from `victims.csv` (`min(loss, tolerance)` over the 115) and match
`results/tables.md` and `docs/methods.md` ($1,544 of $1,582, 98%). The bar fill is 97.6%.

## Governing design and open question

The request names Rahil Design 3.3.2 (charcoal #111214, off-white #F5F5EF, yellow #FFE500, Anton + IBM Plex Sans). The cards
keep that 3.x card family and its tokens, read from the rahil-design bundle (4.0.1) in the hub. The bundle's current
direction is the 4.0 exhibit look (Archivo + IBM Plex Mono), and it keeps Anton only for cards released before 4.0, so
using Anton on these cards rests on the request, not on a 4.0 rule. Rahil should confirm whether Oct 28 stays in 3.x or
moves to a 4.0 exhibit. This replaces the uncommitted 4.0 exhibit specs of cr-97fa84dd (`scripts/x_cards.py` there), which are not included.

## Checks run

- `python -m pytest -q`: 27 passed (22 existing + 5 in `tests/test_x_cards.py`: verbatim text, numbers vs `summary.json`, alt text).
- `design_check.py lint scripts/x_cards.py`: exit 0.
- Render gate in `x_cards.py` (Firefox): no overflow, no wrapped figure label, both fonts loaded, title 3 lines (replay) and 2 lines (slippage).
- `design_check.py feed brief.json` at the 326px feed box (a 360px phone):
  - slippage: labels 18.4px, title 40.1px: **ok**.
  - replay: labels 15.5px, title 40.1px: **fails the 18px label floor**. The requested title (3 lines), panel label (2 lines) and
    footer (2 lines) plus the figure cannot fit a 1080×1080 card at 22px labels. Labels are drawn at 18.5px of 390 (about 16.9px
    in a 390px feed). Shortening the panel label or footer, or dropping one of 0%/mean labels, would restore it; that is a copy decision, so it is left as drafted.
- Looked at both cards at 1080px and downscaled to 360px and 390px.

Not run: the dataviz colour validator, a cold read, Chart Reviewer, a human five-second test, a live X crop. The tick (#111214 on
#76787D) is about 4.2:1; the other colours are existing tokens.

## Artifact hashes (SHA-256)

- `wed28-am-mev/card.png` `5677b7d014a3430b8a7b1bd6dfaf211d1ee08210b8a32dce0be7555ebab39ddd`
- `wed28-pm-mev-slippage/card.png` `97b05e521a4827023682aa05b25892d2153456e972cb8f0c3500fb906d19354e`
