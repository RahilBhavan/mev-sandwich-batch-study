## Table 1. Sandwiches and victim losses, Uniswap v3 SIMD/WETH 0.01%, 2026-10-05 to 2026-10-11 UTC

| Detection tier | Sandwiches | Victims | Victim volume | Victim loss (a) | Attacker gross (b) | Attacker gas | Median loss per victim |
|---|---:|---:|---:|---:|---:|---:|---:|
| All detected (back-run 90–110% of front-run) | 240 | 242 | $29,318 | $1,330 | $1,190 | $2,160 | $2.92 |
| Strict amount match (±1%) | 237 | 239 | $29,027 | $1,327 | $1,187 | $2,157 | $3.02 |
| Strict, single-pool front-run, same EOA | 209 | 211 | $26,146 | $1,188 | $1,062 | $963 | $3.07 |

Loss measure (c), slippage tolerance available to the attacker, is defined for the 15 victims whose router calldata decodes with a non-zero bound: their tolerance totalled $79 and the attackers took $79 of it (100%); the median victim lost 100% of their own tolerance. 1 decoded victims set no minimum at all.

## Table 2. The same blocks under Chan–Wu–Shi per-block clearing

Share of victim loss (a) recovered, each victim capped at its own loss. Static = the same orders replayed; deterred = the attacker's orders removed, because under the mechanism they lose money.

| Detection tier | Attacker net under mechanism, max over all runs | Attacker net, median per sandwich | Deterred | Static, arrival order | Static, random tie-break (mean) | Static, attacker legs without limits (random mean) | Static, every order unlimited |
|---|---:|---:|---:|---:|---:|---:|---:|
| All detected (back-run 90–110% of front-run) | $-0.00 | $-13.59 | 100.0% | 50.3% | 73.4% | 97.7% | 97.3% |
| Strict amount match (±1%) | $-0.00 | $-14.93 | 100.0% | 50.2% | 73.4% | 97.7% | 97.3% |
| Strict, single-pool front-run, same EOA | $-0.00 | $-15.04 | 100.0% | 50.3% | 73.4% | 97.6% | 97.3% |

Across 200 random tie-break draws (all detected), the static share's 5th–95th percentile is 68.6%–77.9%; with the attacker's legs unlimited it is 94.6%–97.7%. Charging the 0.01% pool fee in phase 1 gives 50.3% (arrival order). Smallest victim fill in the static arrival run: 54.4%. Phase-1 gains beyond the sandwich loss (deterred case): $6.31.

## Table 3. Who the victims traded through (all detected)

| Victim transaction target | Victims | Loss (a) |
|---|---:|---:|
| Other targets (bots, smart wallets, smaller routers) | 241 | $1,328 |
| Uniswap Universal Router | 1 | $1 |

Labels are the contracts' Etherscan name tags or public deployment lists (Universal Router v2.1.1/v2.1.2 tags read 2026-10-17).
