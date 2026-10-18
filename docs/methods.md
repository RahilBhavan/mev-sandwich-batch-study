# Sandwich losses on one Uniswap pool, and what per-block two-phase clearing would have prevented

Methods note, 17 October 2026. All numbers come from `results/` and are reproduced by `scripts/run_all.sh`.

## Question and answer

**Question.** In one week, how many swaps on Uniswap v3 WETH/USDT 0.01% were sandwiched, how much did the victims lose, and how much of that loss would Chan, Wu and Shi's per-block two-phase mechanism (AFT 2025, arXiv 2402.09357 v3) have prevented?

**Answer.**
- **The attacks.** From 5 to 11 October 2026 the pool had 70,669 swaps. 236 sandwiches hit 244 victims, who lost **$12,387** against what they would have received with no front-run.
- **Who profits.** Attackers grossed $8,713 on the pool and paid at least $4,400 of it, 50%, as gas charged to this pool. Most of that goes to block builders as priority fees.
- **The attack under the mechanism.** Replayed through the mechanism, no sandwich makes money for its attacker. All 236 lose money in arrival order, and the best case across every ordering and variant is exactly $0.
- **The victims.** If attackers stop because the attack no longer pays, victims recover essentially 100% of the loss. If the identical orders were submitted anyway, they recover 52% to 99% depending on assumptions, with a central estimate of 75%.

![Cumulative victim loss](../results/figure.png)

## Data

- **Pool.** Uniswap v3 WETH/USDT, 0.01% fee, `0xc7bBeC68d12a0d1830360F8Ec58fA599bA1b0e9b`.
- **Selection.** Chosen from a one-day scan of nine popular pools (`docs/pool-selection.md`). It was the busiest of those nine and the only one with regular sandwiches. A later scan of every pool on 7 October showed the list missed v3 USDC/WETH 0.01%, which has about 2.4 times the swaps and is sandwiched about as often. So the study pool is the busiest *WETH/USDT* pool, not the busiest pool overall. The pattern is by fee tier: both 0.01% blue-chip pools are sandwiched about 40 times a day, while their 0.05% pools almost never are.
- **Week.** Monday 5 to Sunday 11 October 2026 UTC: blocks 26,122,440–26,172,657.
- **What was pulled.** Swap, Mint and Burn logs, every transaction that touched the pool (sender, target, input data; 69,058 transactions), and the pool's starting state at block 26,122,439. The starting state is `slot0`, `liquidity`, and the 248 initialized ticks within 2,000 ticks of any price the week reached.
- **Source.** The free archive endpoint `rpc.mevblocker.io`, pulled on 17 October 2026.
- **Control.** The same detector applied to USDC/WETH 0.05% over the same week found 13 sandwiches in 51,029 swaps (`data/scan/control-week.out`).

## Exact replay

Uniswap v3's integer math is ported to Python in `mev/v3.py`: TickMath, SqrtPriceMath including its 256-bit overflow branches, SwapMath, tick-bitmap word boundaries, and the swap loop. The protocol fee is left out because it does not change swap amounts.

**Gate.** The replay must reproduce every swap of the week exactly, matching both amounts and the post-swap (sqrtPriceX96, liquidity, tick). For each swap it tries four order types in turn: exact input, exact output, and each of those stopped by a price limit.

**Result.** 70,669 of 70,669 swaps match, 4,041 of them across liquidity changes.

**Negative controls.**
- A wrong fee breaks 70,645 swaps.
- Dropping the 20 ticks nearest the start price breaks 1,284.
- Ignoring the 129 liquidity events breaks 334.

## Detection

The rule is in `mev/detect.py`; it follows Qin, Zhou and Gervais (S&P 2022) and the Dune spellbook.

1. **Legs.** Each transaction becomes one leg per block, its net trade on the pool, and takes one role.
2. **Pattern.** A sandwich is a front-run and a back-run in the same block, front-run first, trading in opposite directions, with at least one victim between them. The victim trades in the front-run's direction, from a different sender, through a different target contract.
3. **Attacker identity.** Both legs come from the same sending address, or go to the same contract with the back-run within ±1% of the front-run's output.
4. **Amount match.** The back-run sells 90–110% of what the front-run bought.

**Robustness tiers** (`results/tables.md`, Table 1):

| Tier | Sandwiches | Victim loss |
|---|---:|---:|
| All detected | 236 | $12,387 |
| Strict ±1% amount match | 193 | $10,428 |
| Strict, single-pool front-run, same address | 178 | $10,043 |

**Precision.** I read the on-chain evidence for 30 randomly drawn hits row by row (`results/precision-review.md`):
- 25 are textbook sandwiches.
- 3 are jaredfromsubway attempts that lost money on this pool.
- 2 have front-runs that also route through other pools.
- None was a trade that didn't hurt the victim.

**Attackers.** 23 sending addresses appear. On-chain ENS reverse records identify the two largest:

| Attacker | Sandwiches | Victim loss |
|---|---:|---:|
| jaredfromsubway.eth | 96 | $5,086 |
| mevrevolutionx.eth | 56 | $1,815 |
| Third (no ENS name) | 33 | $3,719 |

**Etherscan check.** I read 15 transaction pages covering 5 hits on etherscan.io. All 5 are sandwiches: the pages match the RPC data, attacker contracts carry Etherscan's MEV-bot name tags, and block positions are front-run, then victim, then back-run.

The check found the just-in-time liquidity pattern and the builder bribes. Both are now handled or stated (see (b)).

**Dune's rule, re-implemented.** The public spellbook macros were run locally on the same logs (`scripts/dune_rule.py`, `results/dune-rule-replication.md`).
- Dune's rule confirms 235 of the study's 236 sandwich blocks (99.6%), and 242 of its 244 victims.
- It flags 20 more blocks, all of which fail the study's 90–110% amount check, so the headline count is conservative.
- No Dune account was used; a run of `docs/dune/sandwiches.sql` on Dune itself remains possible.

## Loss measures

- **(a) Counterfactual loss, the headline.** Replay the block from its starting state with every attacker swap and liquidity change removed, re-executing each remaining swap with the amount it specified. The victim's loss is no-attack output minus actual output, or for exact-output swaps, actual input minus no-attack input. Amounts are valued at the block's starting price, with USDT taken as $1.
  - The median victim lost $14.13.
  - The 20 largest sandwiches carry 64% of the week's loss.
  - The largest single loss was $1,714, on a $17,637 sale that had no minimum output.
- **(b) Attacker gross.** Every WETH and USDT transfer between the pool and the attacker's two transactions, valued at the starting price: $8,713.
  - This includes just-in-time liquidity. In 37 sandwiches the attacker also adds liquidity in the front-run and removes it, with fees, in the back-run.
  - Gas from receipts: $4,400. When a leg also trades in other pools, only this pool's share of its swaps is charged here.
  - Payments to builders by internal ETH transfer need traces and are not counted. Etherscan shows them (for example, 0.251 ETH to Titan Builder in block 26164108). So (b) net of gas is an upper bound on what attackers kept.
- **(c) Slippage tolerance available.** The no-attack output minus the victim's own minimum output, from decoded router input data.
  - Defined for 115 victims, whose tolerance totalled $1,582.
  - Attackers took $1,544 of it (98%), and the median victim lost 100% of their own tolerance. Attackers size the front-run to push each victim exactly to its minimum.
  - Another 29 decoded victims had set no minimum at all.

## The mechanism counterfactual

**Implementation** (`mev/mechanism.py`). Figure 1 of the paper, run on the exact v3 pool:
- r0 is the pool's marginal price at the start of the block. Orders whose limit is worse than r0 are dropped.
- Each order is sized in WETH at r0, using the paper's β.
- Phase 1 fills the minority side completely at r0 against the dominant side in tie-break order, splitting the boundary order. The pool does not move.
- Phase 2 executes the rest of the dominant side one order at a time with `sqrtPriceLimitX96` at the order's limit, which is exactly "fill until the marginal rate reaches the limit".
- The paper has no swap fee. Phase 2 keeps the pool fee, and phase 1 is run both without and with it.
- Tests check one-sided blocks against sequential Uniswap swaps, balanced blocks (pool unchanged, all fills at r0), the drop rule, phase-2 limits, and Theorem 3.1 on 200 random sandwiches across three fee levels.

**Orders.** Every swap in a sandwich block becomes an order.
- **Type and amount** come from decoded router input data where it decodes and agrees with the log: Universal Router, SwapRouter02 and SwapRouter, including multicall. Otherwise they come from the replay.
- **Limits.** Uniswap limits bound the *average* price; the paper's limit is *marginal*. The average limit is used as a marginal one, net of the 0.01% fee. Where no limit decodes, the executed average price is used, a price the trader is known to have accepted.
- **Coverage.** A victim's limit applies to this pool only if it was set on this pool's hop (Uniswap routers), or if its whole route was this pool (checked from the victim's receipt). That is true for 160 of the 244 victims; the other 84 route through several pools.
  - Limits were decoded for 144 of those 160 (90.0%; 29 of them with no minimum).
  - Sources: Universal Router, SwapRouter02 and SwapRouter calls, including router calls nested in smart-wallet batches; 1inch v6, KyberSwap, LI.FI, 0x Settler and router `0x8feab81d…` for single-pool routes.
  - Each aggregator decode must match the logs: the specified input equals the pooled input (up to a 1% aggregator fee) or the destination token matches, and the minimum cannot exceed the actual output.
  - All other victims use the executed price.
  - Across all 1,182 swaps in sandwich blocks, coverage is about 15%. 518 of those swaps are the attackers' own legs and most of the rest are bots; neither has public calldata.

**Results** (`results/tables.md`, Table 2):

| Variant | Share of loss (a) recovered |
|---|---:|
| Deterred: attacker orders removed | 100.0% |
| Same orders, arrival order | 51.7% |
| Same orders, random tie-break (mean of 200; 5th–95th percentile 67.8%–84.0%) | 75.5% |
| Same orders, attacker legs without limits (random mean; 87.4%–99.0%) | 93.6% |
| Same orders, every order without a limit | 87.6% |
| Same orders, pool fee charged in phase 1 | 51.7% |

**The attacker.** Under every variant and every draw, no sandwich makes money. In arrival order all 236 lose, with a median of −$15.72 per sandwich. The −$469k total is dominated by a few very large front-runs and is not a meaningful sum.

**Why the static share is below 100%.** The mechanism does not stop a trade ahead of the victim from moving the price within phase 2. It removes the profit. With the attacker's own executed prices as limits, the back-run's limit is worse than r0 and is dropped. The front-run then fills only until the marginal price reaches its own average price, about half its size. The victim, behind it in arrival order, still pays that half.

When the back-run has no limit, it joins the opposite side and is matched against the front-run at r0 in phase 1, so the front-run never touches the pool. That is the mechanism working as designed, and it is why recovery jumps to 87–99%. Random tie-breaking puts the victim ahead of the front-run about half the time.

**Two further results.**
- Phase-1 gains beyond the sandwich loss totalled only $25.60. These blocks have little opposite-side flow.
- Partial fills were rare: one victim filled less than fully (82.8%) in the arrival-order run.

## Extension: a memecoin pool (SIMD/WETH 0.01%)

The same pipeline, unchanged except for the pool configuration (`STUDY_POOL=simd-weth`), was run on the most-sandwiched v3 pool of 7 October: SIMD/WETH 0.01% (`0x7c0cfa93c65733bf2034900fdc672673c4fa4e71`). Results are in `results/simd-weth/`.

- **Pool lifetime.** The pool was created on 6 October at block 26,133,397, during the week. Its state was rebuilt from its `Initialize` event and every later Mint and Burn. All 13,052 swaps replay exactly.
- **Sandwiches and losses.** 240 sandwiches hit 242 victims (237 at the strict ±1% match), who lost **$1,330** on $29,318 of volume. The median victim lost $2.92.
- **One victim dominates.** 199 of the 242 victims are a single automated buyer: an EIP-7702 smart account (`0x2786ed4c…`), sent by one relayer. It bought SIMD 199 times, at a median $70 per trade, and lost a median $3.48 each time, about 5%. That account carries 95% of the pool's loss. Only 19 distinct senders were sandwiched in the week.
- **Attackers.** Gross on this pool was $1,190, against $2,160 of gas charged to it. The two largest attackers are jaredfromsubway.eth (87) and `0x1111…3911` (86).
- **Under the mechanism.** No attack makes money in any run. Victims keep 73% of their loss on average across random tie-breaks (5th–95th percentile 69–78%), 50% in arrival order and 98% with the attacker's legs unlimited. They keep 100% if attackers stop.
- **Checks.** Dune's rule, re-implemented locally, confirms all 240 sandwich blocks and flags 4 more. Limits decode for 16 victims; the automated buyer's smart-account calls do not decode, so its limits use the executed price.

So the memecoin pool has about as many sandwiches as the blue-chip pool but one-ninth the dollar loss, almost all of it from one bot that keeps trading with loose slippage. The mechanism's effect is almost the same in both pools.

## Limits

- **Same order flow.** The counterfactual replays the observed orders. Under the mechanism, bots, builders and traders would behave differently. The deterred case assumes attackers simply stop. Working out the actual response is an empirical game the replay can't settle.
- **What the detector misses.** It sees only same-block, single-pool sandwiches. Cross-block and multi-pool attacks are missed, and private-flow attacks are visible but their causes are not.
- **Average limit as marginal limit.** This is conservative for victims in phase 2, and it is what drives the static lower bound.
- **Just-in-time liquidity.** The paper's model has no liquidity changes inside a block. The mechanism runs apply them at the start of the block, and the attacker net under the mechanism counts the attacker's orders only.
- **Assumptions that differ from Uniswap.** The paper assumes no fee, public orders, partial fills and a constant-function curve. Concentrated liquidity is constant-product only within each tick range. The paper's proofs need increasing marginal cost, which v3 satisfies.
- **One pool, one week.** A week is one sample, not an estimate of a yearly rate.

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python pyarrow matplotlib pytest
scripts/run_all.sh
```
