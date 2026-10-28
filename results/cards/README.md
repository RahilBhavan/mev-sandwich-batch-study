# Oct 28 X cards (rahil-design 4.0.1 exhibits)

Two square cards for the Onchain Receipts posts of Oct 28, 2026. They replace the earlier 3.12 phone cards. Numbers
and post text are unchanged; the cards read the figures in `results/summary.json` and `results/tables.md`.

| Card | File | sha256 |
| --- | --- | --- |
| Sandwich replay (Exhibit 023) | `wed28-am-mev.png` | `5666023a8adbd06a045f057bdbe1a31cd5b58731269e14a637e0530515239d15` |
| Slippage tolerance (Exhibit 024) | `wed28-pm-mev-slippage.png` | `898199fd0941a20b592aa010b4016542e20cd1655ea8b4876af9e7b179c259c8` |

Each `*.exhibit.json` is the source spec (the card text, the figure data and the alt text). Both PNGs are 1080x1080,
charcoal `#111214`, off-white `#F5F5EF` and yellow `#FFE500`, set in Archivo and IBM Plex Mono.

The sandwich card needs a `range` form (a run against its spread, the mean as the one yellow marker, `0%` and `100%`
at the axis ends) and a footer ink option that Proof Desk did not have. They are in
`proof-desk-range-form.patch` (a `git format-patch` of one commit for `proof-desk`). Render with that patch applied:

    pd research lint results/cards/*.exhibit.json
    pd research hubspec results/cards/wed28-am-mev.exhibit.json --out OUT/wed28-am-mev
    python social_bars.py OUT/wed28-am-mev/spec.json OUT/wed28-am-mev      # rahil-design scripts

## Status: design review pending

Rahil has not passed these exact bytes. The checks that ran are lint (R1 to R13), the exhibit layout check, the pixel
audit (0.00% of pixels off the tokens), the release gate (form rules, card/post/source agreement), a cold read by a
Haiku reader (title, highlight and every number read back) and a look at 360 px and 390 px.

Limit: at a 360 px feed the exhibit's smallest text (axis ticks, units line, footer) is about 6 px, and
`design_check.py feed` reports 5.4 px labels against its 18 px phone-card floor. The 4.0 exhibit floor is 18 px on the
1080 canvas, so these cards meet the exhibit rules but not the older phone floor.
