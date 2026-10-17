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
- Five attacker EOAs appear. The most frequent, `0xae2fc483…fae13` with 4 hits, is believed to be jaredfromsubway **[label unverified]**.
- Ratios ranged from 0.90 to 1.00. Hits near 0.90 need manual inspection.

## Decision

**WETH/USDT 0.01% Uniswap v3** (`0xc7bBeC68d12a0d1830360F8Ec58fA599bA1b0e9b`):

- It had the most swaps of any pool scanned, so it fits "popular".
- It is the only candidate with regular sandwiches: about 12 a day, about 80 a week projected.
- At 0.01% the fee is so low that the fee question in the paper's fee-free model matters least.

USDC/WETH 0.05% serves as a **control**. Zero sandwiches there is a finding: private order flow and arbitrage have largely moved those attacks elsewhere.

## Before freezing

- Confirm the weekly count with a 7-day count-only run on the chosen pool and the control.
- Freeze a full Monday–Sunday UTC week of block numbers.
- Spot-check 5 hits on Etherscan.
