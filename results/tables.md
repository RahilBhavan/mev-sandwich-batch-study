## Table 1. Sandwiches and victim losses, Uniswap v3 WETH/USDT 0.01%, 2026-10-05 to 2026-10-11 UTC

| Detection tier | Sandwiches | Victims | Victim volume | Victim loss (a) | Attacker gross (b) | Attacker gas | Median loss per victim |
|---|---:|---:|---:|---:|---:|---:|---:|
| All detected (back-run 90–110% of front-run) | 236 | 244 | $576,836 | $12,387 | $6,242 | $5,703 | $14.13 |
| Strict amount match (±1%) | 193 | 199 | $462,210 | $10,428 | $5,526 | $4,079 | $14.13 |
| Strict, single-pool front-run, same EOA | 178 | 183 | $425,710 | $10,043 | $5,358 | $3,733 | $14.40 |

Loss measure (c), slippage tolerance available to the attacker, is defined for the 88 victims whose router calldata decodes with a non-zero bound: their tolerance totalled $1,062 and the attackers took $1,043 of it (98%); the median victim lost 100% of their own tolerance. 27 decoded victims set no minimum at all.

## Table 2. The same blocks under Chan–Wu–Shi per-block clearing

Share of victim loss (a) recovered, each victim capped at its own loss. Static = the same orders replayed; deterred = the attacker's orders removed, because under the mechanism they lose money.

| Detection tier | Attacker net under mechanism, max over all runs | Attacker net, median per sandwich | Deterred | Static, arrival order | Static, random tie-break (mean) | Static, attacker legs without limits (random mean) | Static, every order unlimited |
|---|---:|---:|---:|---:|---:|---:|---:|
| All detected (back-run 90–110% of front-run) | $0.00 | $-15.72 | 100.0% | 51.7% | 75.5% | 93.6% | 87.6% |
| Strict amount match (±1%) | $0.00 | $-15.27 | 100.0% | 51.6% | 75.5% | 92.5% | 85.6% |
| Strict, single-pool front-run, same EOA | $0.00 | $-15.74 | 100.0% | 51.7% | 75.5% | 92.3% | 85.1% |

Across 200 random tie-break draws (all detected), the static share's 5th–95th percentile is 67.8%–84.0%; with the attacker's legs unlimited it is 87.4%–99.0%. Charging the 0.01% pool fee in phase 1 gives 51.7% (arrival order). Smallest victim fill in the static arrival run: 82.8%. Phase-1 gains beyond the sandwich loss (deterred case): $25.60.

## Table 3. Who the victims traded through (all detected)

| Victim transaction target | Victims | Loss (a) |
|---|---:|---:|
| Other targets (bots, smart wallets, smaller routers) | 75 | $6,687 |
| Uniswap SwapRouter02 | 73 | $1,314 |
| Universal Router-style execute() (unlabelled) | 35 | $1,187 |
| 0x AllowanceHolder | 16 | $1,099 |
| KyberSwap MetaAggregationRouterV2 | 16 | $1,032 |
| 1inch Aggregation Router v6 | 5 | $442 |
| LI.FI Diamond | 14 | $347 |
| Uniswap Universal Router | 10 | $280 |

Labels are from the contracts' public deployments; "unlabelled" was not verified.
