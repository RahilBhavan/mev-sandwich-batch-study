# Post cards for Oct 28, 2026 (design review pending)

Two 1080x1080 cards in Rahil Design: charcoal `#111214`, off-white `#F5F5EF`, yellow `#FFE500`, Anton titles, IBM Plex Sans text. These are review drafts. A rendered file, a passing check or a merged PR is not design approval, and nothing here is scheduled or posted.

| Slot | Card | Alt text |
|---|---|---|
| 2026-10-28 09:30 ET | `wed28-am-mev-square.png` | `wed28-am-mev.alt.txt` |
| 2026-10-28 18:00 ET | `wed28-pm-mev-slippage-square.png` | `wed28-pm-mev-slippage.alt.txt` |

`SHA256SUMS` holds the PNG hashes. `feed/` holds the 360px and 390px feed screenshots (2x device pixels, image 328px and 358px wide). `palette-check.txt`, `design-checks.txt` and `measurements.json` hold the check output.

## Regenerate

```
uv run --with playwright==1.63.0 --with pillow --with numpy python scripts/post_cards.py
```

The script reads `results/victims.csv` and `results/summary.json`, draws both cards in Firefox and exits 1 if any check fails. Fonts are in `scripts/post-card-fonts/` (Anton and IBM Plex Sans, both SIL OFL, licences included). A second run gives byte-identical PNGs.

## What the cards say

- MEV (`wed28-am-mev`): title "Replay recovered 75%. Arrival order: 52%." Panel label "Share of $12,387 sandwich loss recovered (counterfactual replay)". Two bars on one 0–100% axis, labelled 0%, 50% and 100%: arrival order 52% (a bar from zero), and random tie-break orders as a bar spanning the 5th–95th percentile (68–84%) with the 75% mean marked in yellow. Footer "Source: mev-sandwich-batch-study replay · busiest WETH/USDT pool, Oct 5–11, 2026".
- Slippage (`wed28-pm-mev-slippage`): title "98% of slippage tolerance taken." Panel label "Slippage tolerance (no-attack output − victim's minimum), 115 of 244 victims with decoded nonzero limits". Tolerance set $1,582, taken by attackers $1,544, share taken 98%. Footer "Source: mev-sandwich-batch-study methods.md · busiest WETH/USDT pool, Oct 5–11, 2026".
- Every number is computed from `results/victims.csv` and `results/summary.json` (arrival 51.7%, mean 75.4%, 5th–95th 67.8%–84.0%, 200 draws). The cards print whole percents, so 75.4% (victims.csv) versus 75.5% (summary.json) cannot differ on the image. The post text is unchanged.
- Footers are #F5F5EF on the charcoal canvas. The earlier "data as of Oct 17, 2026" line is gone: the footer wording is the reviewed one.

## Chart Reviewer fixes applied

| Card | Fix | Where |
|---|---|---|
| MEV | 1080×1080 | PNG size asserted by the script and `palette-check.txt` |
| MEV | 75% mean marker on the random-orders bar | yellow marker at 75.4% on the 68–84% bar |
| MEV | title "REPLAY RECOVERED 75%. ARRIVAL ORDER: 52%." | h1 (Anton, set uppercase) |
| MEV | 0% label at the left end of the axis | axis row, with 50% and 100% |
| MEV | panel label | `.context` |
| MEV | footer in #F5F5EF | `.foot` |
| MEV | alt text | `wed28-am-mev.alt.txt` |
| Slippage | 1080×1080, panel label, footer, alt text | as above |

## Governing design

Built against the Rahil Design 3.x look the request named (3.3.2: charcoal `#111214`, off-white `#F5F5EF`, yellow `#FFE500`, Anton titles, IBM Plex Sans text). The installed bundle is 4.0.1 (Rahil Bhavan Research: Archivo, exhibit frame, from the week of November 2). The 3.x palette and fonts are unchanged here, Anton stays available for released 3.x cards, and no explicit decision from Rahil to move these two Oct 28 cards to 4.x was found. Say if they should be re-made as 4.x exhibits.

Each card is authored on a 390px canvas with 22px text and a 48px title and exported at 1080px. In a 326px feed image that is 18.4px labels and a 40.1px title; at a 360px feed (328px image) 18.5px and 40.4px; at 390px (358px image) 20.2px and 44.1px.

Clutter budget (`references/cards-and-pages.md`): the requested wording does not fit the "title on at most 2 lines, no label that wraps inside the figure, one-line source note" rule at the type floors. The MEV title is 3 lines (it cannot be 2 at 48px in Anton), both panel labels and both footers wrap, and the MEV panel is full. The type was not shrunk below the floors; the wording is the reviewed wording. Shortening it is the way to restore the budget.

## Not done

- No named reviewer has passed these files, so no review record was written (the ledger lives in the hub, outside this repository). No Chart Reviewer pass on these exact bytes, no timed reader test, no cold read. Design review pending.
- The hub content packages (`design-r5/bundles/wed28-am-mev` and `wed28-pm-mev-slippage`, released Oct 27) are outside this repository and were not touched. This directory is the refreshed in-repo package: PNG hashes in `SHA256SUMS` and each `*.brief.json`, alt text in `*.alt.txt`. Swapping the hashes into the hub bundles is a hub-side step.
- Not tested in Chrome or Safari; rendered in Firefox only.
