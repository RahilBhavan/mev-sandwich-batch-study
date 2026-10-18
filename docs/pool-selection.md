# Pool selection

## Scan

- **Run date:** 2026-10-17. **Script:** `scripts/scan_pools.py`. **RPC:** `rpc.mevblocker.io`.
- **Blocks:** 26,207,481–26,214,680, i.e. 7,200 blocks or about 24 hours.
- **Rule:** same block and same pool; front-run and back-run go in opposite directions, with a victim between them in the front-run direction. The attacker matches on the same EOA, or on the same target contract with the amount within ±1%. A sandwich counts only if the back-run sells 90–110% of what the front-run bought (the Qin et al. check).

| Pool | Address | Swaps | Sandwiches | Victims |
|---|---|---:|---:|---:|
| v3 USDC/WETH 0.05% | 0x88e6…5640 | 3,580 | 0 | 0 |
| v3 USDC/WETH 0.30% | 0x8ad5…6eb6 | 372 | 0 | 0 |
| v3 WETH/USDT 0.05% | 0x11b8…97F6 | 2,011 | 0 | 0 |
| v3 WETH/USDT 0.30% | 0x4e68…fa36 | 428 | 0 | 0 |
| **v3 WETH/USDT 0.01%** | **0xc7bBeC68d12a0d1830360F8Ec58fA599bA1b0e9b** | **9,890** | **12** | **13** |
| v3 PEPE/WETH 0.30% | 0x1195…1b58 | 231 | 0 | 0 |
| v2 USDC/WETH | 0xB4e1…9Dc | 586 | 0 | 0 |
| v2 WETH/USDT | 0x0d4a…1852 | 718 | 0 | 0 |
| v2 PEPE/WETH | 0xA43f…c9f | 436 | 0 | 0 |

- One further candidate had an amount ratio outside 90–110% and was excluded.
- One sandwich had two victims.
- Five attacker EOAs appear. The most frequent, `0xae2fc483…fae13` with 4 hits, is jaredfromsubway.eth (verified 2026-10-17 by ENS reverse resolution on chain).
- Ratios ranged from 0.90 to 1.00. Hits near 0.90 need manual inspection.

## Decision

**WETH/USDT 0.01% Uniswap v3** (`0xc7bBeC68d12a0d1830360F8Ec58fA599bA1b0e9b`):

- It had the most swaps of any pool scanned, so it fits "popular".
- It is the only candidate with regular sandwiches: about 12 a day, about 80 a week projected.
- At 0.01% the fee is so low that the fee question in the paper's fee-free model matters least.

USDC/WETH 0.05% serves as a **control**. Zero sandwiches there is a finding: private order flow and arbitrage have largely moved those attacks elsewhere.

## Frozen week (2026-10-17)

- **Week:** Monday 5 October 00:00:00 to Sunday 11 October 2026 23:59:59 UTC = blocks **26,122,440–26,172,657** (50,218 blocks), found by binary search on block timestamps. Recorded in `mev/pool.py`.
- **Chosen pool, full detector** (`scripts/analyze.py`): 70,669 swaps, **236 sandwiches**, 244 victims (193 at the strict ±1% match). That is about three times the one-day projection: the 17 October scan day was quieter, and the full detector merges a transaction's swaps into one leg.
- **Control, USDC/WETH 0.05%, scan detector** (`scripts/scan_pools.py`, via eth.drpc.org in 100-block chunks because rpc.mevblocker.io was rate-limited by the parallel ingest): 51,029 swaps, 13 sandwiches, 20 victims, plus 7 outside the 90–110% amount window. Output: `data/scan/control-week.out`.
- **Spot checks:** 30 random hits reviewed from on-chain evidence in place of 5 Etherscan views (`results/precision-review.md`). A human Etherscan check of five is still open.
