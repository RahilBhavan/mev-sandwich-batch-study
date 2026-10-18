# Plan: sandwich losses on one Uniswap pool, and what per-block batch clearing would have prevented

## Purpose

This is a short measurement study for an opening email to Ke Wu (UMich CSE) and Michael Wellman (UMich CSE). The study takes one week of swaps on one Uniswap pool and does three things:

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

- **"One popular pool" and "many sandwiches" pull against each other.** Blue-chip pools now see almost no sandwiches (see research §7). `docs/pool-selection.md` records the choice and the evidence. A result near zero on a blue-chip pool is a valid finding, but it makes a weaker opener.
- **Describe the design as Ke Wu's paper does:** per-block, two-phase, arbitrage-resilient. It is not a uniform-price auction.
- **This is a counterfactual on the same order flow.** Under a different mechanism, users and bots would behave differently. The study measures the *static* effect on observed orders, and the write-up says so.

## Status (2026-10-17)

Days 1–10 are done except the items that need Rahil (marked ⧗). Results: `docs/methods.md`, `results/`.

| Day | Status |
|---|---|
| 1 Pool selection | Done. Week frozen; 7-day counts for the pool and the control |
| 2 Ingest | Done. 70,669 swaps, 129 liquidity events, 69,058 txs. A rerun gives byte-identical Parquet files; eth.drpc.org returns the same 70,669 swap logs |
| 3–4 Exact simulator | Done. 100% of swaps reproduce; three negative controls break it |
| 5 Detector | Done. 30-hit review. ⧗ Dune cross-check (query and comparison script ready in `docs/dune/`, `scripts/compare_dune.py`), ⧗ five human Etherscan checks |
| 6 Loss measures | Done. (a), (b), (c) |
| 7 Limits from input data | Done for Universal Router, SwapRouter02 and SwapRouter (115 of 244 victims). The ≥ 90% target was not met: the rest trade through aggregators and smart wallets, which use the executed-price fallback |
| 8–9 Mechanism | Done. Attacker net ≤ 0 in every run; prevented-share table |
| 10 Write-up | Done. Figure (present-data brief passes), methods note, two email drafts in `outreach/` (gitignored). ⧗ Rahil's review, publish decision and send |

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
| 10 | Figure, methods note, README, email draft. Peer check by rereading the paper's §3. | Draft email and two-page summary ready for Rahil to review |

If the work slips, cut in this order: Universal Router decoding (fall back to the executed-price bound), then multiple random draws (use arrival order), then the second loss measure.

## Validation and limits

- Run the simulator on every observed swap before any counterfactual.
- Spot-check detection by hand, and compare with the Dune spellbook in one trial session.
- Record each RPC used, the block range and the run date.
- Limits to state: same-block, single-pool detection only; private-flow attacks are visible but their causes are not; no behavioural response; paper assumptions (fee-free model, partial fills, public orders) differ from Uniswap's.

## Outreach (not started; needs Rahil's approval before sending)

- Draft with the `outreach-email` skill once the numbers exist.
- Lead with one sentence of measurement, then the prevented share and one question about the paper. Examples: how the guarantees carry over to concentrated liquidity, or the all-or-nothing open problem.
- For Wellman: frame the work as the DEX version of the frequent call market versus continuous trading question from Wah & Wellman (2016).
- Publishing the repository and sending email are separate decisions.
