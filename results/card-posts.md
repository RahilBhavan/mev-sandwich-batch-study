# Post text for the two cards (drafts)

Draft wording for the 2026-10-28 posts, matched to the cards. These are drafts, not scheduled or posted. The content package lives outside this repository and has not been changed.

## MEV post (2026-10-28 09:30 ET), `mev-get-back-square.png`

> Oct 5 to 11, 2026, the busiest WETH/USDT pool on Uniswap v3: 70,669 swaps, 236 sandwiches, 244 victims, $12,387 lost against no front-run. Replayed through a per-block batch mechanism (Chan, Wu, Shi), no sandwich made money. Victims got back 75% of their loss on average over 200 random tie-breaks.

Change from the current text: "Victims kept 75% of their loss on average" is now "Victims got back 75% of their loss on average over 200 random tie-breaks".

## Slippage post (2026-10-28 18:00 ET), `slippage-taken-square.png`

> Slippage tolerance reads like a safety setting. On the busiest WETH/USDT pool, Oct 5 to 11, across the 115 sandwiched victims whose minimum output could be decoded and was non-zero, attackers took 98% of that tolerance ($1,544 of $1,582). The setting works more like a price you agree to pay if you're picked.

Change from the current text: it now names the 115 victims and the dollars. The current alt text says "144 sandwiched swaps". 144 counts every victim with a decoded limit, including 29 who set no minimum; the 98% is over the 115 with a non-zero one (README, `results/tables.md`).

Alt text for both cards is in `card-alt-text.md`. PNG hashes are in `cards.sha256`.
