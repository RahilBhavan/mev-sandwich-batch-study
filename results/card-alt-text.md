# Card alt text

Written by `scripts/card.py` from the rows each card draws; the landscape and square cards carry the same rows.

## mev-get-back-square.png and mev-get-back-landscape.png

Per-block clearing hands victims back about 75% of a week’s $12.4k sandwich loss. No sandwich made money under batch clearing. Same orders, arrival order: 52%. Same orders, random tie-break (mean of 200): 75% (p5-p95 68-84%). Attacker, no slippage limit (arrival): 87%. Every order, no slippage limits (arrival): 88%. If attackers stay out: about 100%. Source: Ethereum logs via rpc.mevblocker.io, as of 17 Oct 2026.

## slippage-taken-square.png and slippage-taken-landscape.png

Attackers took 98% of the slippage victims allowed. 115 of 244 victims set a decodable, non-zero minimum; 29 more set none and are left out. Tolerance the 115 victims set: $1,582. Taken by the attackers: $1,544, 98%. Source: Ethereum logs via rpc.mevblocker.io, as of 17 Oct 2026.
