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

- MEV: arrival order 51.7%, random tie-breaks (mean of 200) 75.4%, 5th–95th percentile 68%–84%, share of the $12,387 loss, same orders, one WETH/USDT pool, Oct 5–11, 2026.
- Slippage: attackers took $1,544 of $1,582 tolerance, 98%, summed dollars rather than a median, across the 115 of 244 victims whose decoded limit was not zero.
- Both footers give the source (`mev-sandwich-batch-study`) and "data as of Oct 17, 2026", the date the results were generated (`results/` commit of 2026-10-17).

## Governing design

Built against `rahil-design` 3.10.0, the version installed when this was made (tokens read from the bundle). The request named 3.3.2; the palette and fonts are the same, and the feed floors (18px labels, 40px title as displayed in a 326px image) are checked here. No explicit user override of the design system was given.

Each card is authored on a 390px canvas with 22px text and a 48px title and exported at 1080px. In a 326px feed image that is 18.4px labels and a 40.1px title; at a 360px feed (328px image) 18.5px and 40.4px; at 390px (358px image) 20.2px and 44.1px.

## Not done

No named reviewer has passed these files, so no review record was written (the ledger lives in the hub, outside this repository). No timed reader test. Post copy in the hub package is untouched; the cards were compared with it by hand (see the PR).
