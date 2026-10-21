# Plan: sandwich losses on one Uniswap pool, and what per-block two-phase clearing would have prevented

## Purpose

This is the plan for a short measurement study. It records the question, the acceptance criteria for each step and the status. The study takes one week of swaps on one Uniswap pool and does three things:

1. Count the sandwich attacks.
2. Estimate how much the victims lost.
3. Replay every block through the Chan–Wu–Shi swap mechanism (AFT 2025) to estimate how much of that loss it would have prevented.

The research inputs are in `docs/research.md`, and the pool choice is in `docs/pool-selection.md`.

## Question and outputs

**Question.** In one week, how many swaps on pool P were sandwiched, how much did the victims lose, and what share of that loss would per-block two-phase clearing (Chan, Wu, Shi 2025) have prevented?

**Outputs**

1. A table with the number of sandwiches, number of victims, victim loss under measures (a), (b) and (c) in USD with ranges, attacker net profit, and the share of victim volume affected.
2. A table comparing mechanism outcomes: attacker net under the mechanism (theory predicts ≤ 0), victim outcome against the status quo, share of loss prevented with its 5–95% range across random orderings, the extra gain from phase-1 matching, and the unfilled volume.
3. One figure: victim loss per sandwich under the status quo against under the mechanism. Follow `present-data` and `tufte-graphics`.
4. A methods note of at most 4 pages covering the detection rule, the loss definitions, the simulator validation and the limits.
5. Public code that reproduces everything from a block range.

## Decisions to keep explicit

- **"One popular pool" and "many sandwiches" pull against each other.** Blue-chip pools now see almost no sandwiches (see research §7). `docs/pool-selection.md` records the choice and the evidence. A result near zero on a blue-chip pool is a valid finding, but it is a weaker result.
- **Describe the design as Ke Wu's paper does:** per-block, two-phase, arbitrage-resilient. It is not a uniform-price auction.
- **This is a counterfactual on the same order flow.** Under a different mechanism, users and bots would behave differently. The study measures the *static* effect on observed orders, and the write-up says so.

## Status (2026-10-17)

Days 1–10 are done. Results: `docs/methods.md`, `results/`.

| Day | Status |
|---|---|
| 1 Pool selection | Done. Week frozen; 7-day counts for the pool and the control |
| 2 Ingest | Done. 70,669 swaps, 129 liquidity events, 69,058 txs. A rerun gives byte-identical Parquet files; eth.drpc.org returns the same 70,669 swap logs |
| 3–4 Exact simulator | Done. 100% of swaps reproduce; three negative controls break it |
| 5 Detector | Done. 30-hit evidence review, and 5 hits (15 pages) checked on Etherscan, which found just-in-time liquidity in 37 sandwiches (now handled). Dune's spellbook rule re-implemented locally on 2026-10-18 (no account): it confirms 99.6% of sandwich blocks; it flags 20 more, all outside the amount window (`results/dune-rule-replication.md`) |
| 6 Loss measures | Done. (a), (b), (c) |
| 7 Limits from input data | Done. 144 of the 160 victims whose limit is attributable to this pool (90.0%). Sources: Uniswap routers, routers nested in smart-wallet batches, and 1inch, KyberSwap, LI.FI, 0x and `0x8feab81d…` for single-pool routes. The literal target, ≥ 90% of all swaps in sandwich blocks, is unreachable by construction: 518 of the 1,182 are attackers' own legs and most of the rest are bots without public calldata (about 15% decode). The other 84 victims route through several pools, so their bounds cannot be attributed to this pool |
| 8–9 Mechanism | Done. Attacker net ≤ 0 in every run; prevented-share table |
| 10 Write-up | Done. Figure (present-data brief passes), methods note and README. The repository has been public on GitHub since 2026-10-18 |

**Extension and risks (2026-10-18)**
- *Free endpoint:* resolved. The week downloaded from rpc.mevblocker.io, and eth.drpc.org returned the same 70,669 swap logs.
- *Exact replay:* resolved. It is exact on the first try for both pools, including tick crossings and a pool created mid-week.
- *Small result:* did not occur (236 sandwiches, $12,387). The optional memecoin extension was run anyway, at Rahil's request, on SIMD/WETH 0.01%: 240 sandwiches and $1,330 lost (`docs/methods.md`, extension section).
- *Pool choice:* corrected. A full scan of 7 October showed the nine-pool list missed USDC/WETH 0.01% (`docs/pool-selection.md`).

## Schedule (10 working days)

| Day | Work | Done when |
|---|---|---|
| 1 | Pool selection: one-day scan of 9 candidates, then confirm the chosen pool over 7 days with counts only. Freeze the week's block range. | `pool-selection.md` names the pool and the block range |
| 2 | Ingest: Swap/Mint/Burn logs, txs (from, to, input), receipts (gas), base fee and builder, saved as Parquet. Make it idempotent and resumable. | Rerunning gives identical files, and the swap count matches a second RPC |
| 3–4 | Exact v3 integer swap simulator (TickMath, SwapMath, tick crossing from archive `ticks()`). | Reproduces **100%** of observed swaps in the week exactly, or every mismatch is explained |
| 5 | Sandwich detector at both thresholds, tested against hand-labelled cases and a Dune trial cross-check. | Precision checked on 30 random hits by Etherscan inspection; agreement with Dune reported |
| 6 | Loss measures (a), (b), (c), with USD conversion at block time from the pool price. | Each sandwich has three loss numbers; totals reconcile |
| 7 | Calldata decoding for limits (SwapRouter02, Universal Router V3_SWAP_EXACT_IN/OUT, v2 router). | Limit decoded for ≥ 90% of swaps in sandwich blocks; the rest are flagged |
| 8–9 | Mechanism simulator: phase 1 at r0, phase 2 using v3 math with price limits, random tie-breaking with ≥ 200 draws, fee sensitivity. Unit tests use the paper's own examples and theorem checks. | Attacker net ≤ 0 in every simulated block; prevented-share table produced |
| 10 | Figure, methods note, README. Peer check by rereading the paper's §3. | Methods note and figure ready for Rahil to review |

If the work slips, cut in this order: Universal Router decoding (fall back to the executed-price bound), then multiple random draws (use arrival order), then the second loss measure.

## Validation and limits

- Run the simulator on every observed swap before any counterfactual.
- Spot-check detection by hand, and compare with the Dune spellbook in one trial session.
- Record each RPC used, the block range and the run date.
- Limits to state: same-block, single-pool detection only; private-flow attacks are visible but their causes are not; no behavioural response; paper assumptions (fee-free model, partial fills, public orders) differ from Uniswap's.
