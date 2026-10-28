# X cards, Wed Oct 28 (wed28-am-mev, wed28-pm-mev-slippage)

**Design review pending.** Nobody has passed these exact bytes; Chart Reviewer and Rahil still decide. Rendered drafts, a green CI run and a merged PR do not approve publication.

| Card | File | SHA-256 |
| --- | --- | --- |
| wed28-am-mev | `wed28-am-mev/card.png` (1080×1080) | `5c09d4e1d40178b65256b2c73dff75e733184c84726423d09697b3ca1861c4af` |
| wed28-pm-mev-slippage | `wed28-pm-mev-slippage/card.png` (1080×1080) | `7ffaa8045695a999cc2d4d9b9a7cb03ae1358f1379dbde22d862f255e759ffd7` |

Each folder also holds `spec.json` (the card spec), `alt.txt` (the alt text) and `brief.json` (the renderer's measurements).

## Governing design

rahil-design **4.0.1** (Rahil Bhavan Research, approved Oct 27, 2026), phone-card path: charcoal `#111214`, off-white `#F5F5EF`, yellow `#FFE500`, display type set in Archivo 800 at 62% width, IBM Plex Sans for labels. The request named 3.3.2 with Anton; 4.0.0 retired Anton and the 3.3.2 renderer, and the tokens are unchanged, so the colours match. This is a font difference to confirm, not a silent choice: if Rahil wants Anton back, that is a design-system decision, not a card edit.

## What the cards say

- **wed28-am-mev**, "Order matters.": arrival order 52%; 200 random tie-breaks, mean 75%, 5th–95th percentile 68–84%; basis $12,387 of sandwich loss.
- **wed28-pm-mev-slippage**, "98% of the tolerance, taken.": 115 of 244 victims, $1,582 tolerance, $1,544 taken, $38 left.
- Both footers: WETH/USDT · Oct 5–11, 2026.

Every figure is built by `scripts/x_cards.py` from `results/summary.json` and `results/victims.csv` (taken = $1,543.96 and tolerance = $1,581.69 over the 115 victims with a decoded nonzero limit; left = $37.73). `tests/test_x_cards.py` pins them. Whole percentages only: `summary.json` stores the mean as 0.7545, which `docs/methods.md` prints as 75.5% and the earlier card's alt as 75.4%; 75% matches the post.

## Limits

- **Repo link is not on the image.** The phone card allows a one-line source note (about 30 characters at the 22px floor), so pool and date fit and the URL does not. The link is in each `alt.txt` and in the post replies. An exhibit-frame render (footer with the URL) was tried and fails the feed floor: labels 5.4px on a 326px feed against 18px.
- **$38 and $1,582 are not in the post text or its replies** (they are in the previous card and the new alt). The release gate wants every number on a card in the post, a reply or the alt; the alt covers it, and the post text is unchanged as requested.
- **Series tag / exhibit number** are not used on the phone card.

## Checks run (Oct 28, 2026)

- `design_check.py card` and `lint` on each spec and card.html: ok.
- `design_check.py feed` on each brief: labels 18.4px, point 40.1px at a 326px content box (360px feed); 20.1px labels at 390px. ok.
- `pixel_audit.py` on each PNG: 0.00% of pixels off-system.
- Inspected the 1080 PNGs and 360px and 390px downscales: titles, bars and labels read; nothing clips.
- `python -m pytest -q`: 25 passed.
- Not run: `post_consistency.py`, cold read, `review_record.py` (no named reviewer; needs the post package).

## Rebuild

```
python scripts/x_cards.py
# from the hub (~/.t3/projects/main), for each card:
uv run --with playwright==1.63.0 --with fonttools python .agents/skills/rahil-design/scripts/social_bars.py results/x-cards/<id>/spec.json <out-dir>
```
Copy `card.png` and `brief.json` back into `results/x-cards/<id>/`.
