# Design system for the study's post cards

This file governs the two post cards that `scripts/card.py` draws: the MEV card (`results/mev-get-back-*.png`) and the slippage card (`results/slippage-taken-*.png`). It is the design Rahil's Chart Reviewer asked for on 2026-10-26. It does not change any other project's design.

## Rules

- **Colour.** Navy `#0b1f4b` on white `#ffffff`. Red `#c8102e` marks the single highlighted series, the one value the title or label names. Every other bar is navy. White text sits on the bars.
- **Type.** Roboto Slab Bold for titles. Archivo (Regular for body, SemiBold for labels and bar values) for everything else. Font files and licences are in `scripts/card-fonts/`.
- **Size.** Design at 1024px wide. All text is at least 26px at that width (`MIN_TEXT_PX`; `card.py` refuses to draw anything smaller). Titles are 34px (landscape) and 48px (square).
- **Formats.** Each card exports at exactly 1024x640 (landscape) and 1024x1024 (square) px, 100 dpi, with the same rows in both.
- **Title.** The title states the takeaway and leads with the number it highlights. A subtitle adds one qualifier.
- **Chart.** Bars start at zero and share one scale, with a 0 and 100% axis and a plain-words axis label. Each row has its label above the bar and its value inside it. No legend, grid or shadow.
- **Footer.** Two lines: the pool and week, then the source and the date the data is as of.
- **Alt text.** `card.py` writes `results/card-alt-text.md` from the same rows it draws, so the alt text and the card agree row for row.
- **Hashes.** `card.py` writes `results/cards.sha256`; a test checks that the committed PNGs match it.

## Wording on the cards

- Say victims "get back" a share of their loss, never "keep" it.
- The last MEV bar reads "If attackers stay out: about 100%". Do not print ">99%" or "99.99%".
- Say "tie-break (mean of 200)" and give the p5-p95 range in the label of the highlighted bar.
- Use one victim count for slippage: **115** victims whose decoded limit is non-zero (their $1,582 tolerance, of which attackers took $1,544, 98%). The 144 in `results/summary.json` counts all victims with a decoded limit, including 29 who set no minimum, so it has no tolerance to take.

## Status and open conflict

These cards follow the request that asked for navy and red with Roboto Slab and Archivo. The shared public system, `rahil-design` 3.3.1, is charcoal, white and yellow with Anton and IBM Plex Sans, floors feed text at 18px in a 356px-wide feed, and says social cards carry no navy panels. At 356px the 26px text here is about 9px. No current instruction from Rahil choosing one over the other was found, so the cards are review drafts: **design review pending**. Do not post them or put them in a content package until that choice is made.
