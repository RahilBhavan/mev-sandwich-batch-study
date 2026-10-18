# Research notes (2026-10-17)

These are the inputs the study rests on. Claims carry sources. Items marked **[unverified]** have not been checked against a primary source. The PDFs cited are kept locally in `references/` (gitignored).

## 1. The design being tested

**Paper:** T-H. Hubert Chan, Ke Wu, Elaine Shi, "Mechanism Design for Automated Market Makers". AFT 2025, LIPIcs vol. 354, 7:1–7:22, [DOI 10.4230/LIPIcs.AFT.2025.7](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.AFT.2025.7). Full version: [arXiv 2402.09357](https://arxiv.org/abs/2402.09357), v3 of 2025-09-13. Author order is randomized. Section numbers below refer to arXiv v3.

This is Ke Wu's only paper that batches DEX orders per block to stop front-running. Her other papers are about transaction fee mechanisms ([2209.14462](https://arxiv.org/abs/2209.14462), [2302.12895](https://arxiv.org/abs/2302.12895), [2501.03141](https://arxiv.org/abs/2501.03141), and the 2026 papers [2609.32005](https://arxiv.org/abs/2609.32005) and [2610.00697](https://arxiv.org/abs/2610.00697)). Her position: Assistant Professor, UMich CSE ([MICL story, Feb 2025](https://micl.engin.umich.edu/stories/ke-wu-receives-stellar-academic-research-grant)).

**It is not a uniform-price batch auction.** §1.2 states that "batch clearing at uniform price [CF23, CF24, cow] does not automatically guarantee incentive compatibility". The outreach must not describe it as a uniform-price design.

**The mechanism (§3.1, Figure 1).** Its input is one block's orders on one two-asset pool. Each order is (type, max amount v, limit rate r).

1. Set r0 = the pool's marginal rate at the start of the block. Drop every order whose limit is worse than r0.
2. Sum the remaining orders at r0 to find the dominant side.
3. Phase 1 matches the minority side fully against an equal amount of the dominant side, all at r0. The pool does not change. The order at the boundary is split.
4. Phase 2 executes the rest of the dominant side one order at a time along the curve. Each order fills as far as possible until the marginal rate reaches its limit. Orders fill partly, not all-or-nothing.
5. Tie-breaking within a side uses trusted randomness or arrival time (§3.1, §3.3).

**Guarantees.**

- *Arbitrage resilience* (Def. 2, Thm 3.1). No coalition, including a block producer that inserts, drops or reorders orders, can make a risk-free profit (Remark 1).
- *Incentive compatibility* (Def. 3, Thm 3.2). This holds only in the weak fair-sequencing model (§2.4), and the mechanism is not incentive compatible in the plain model (§3.3).
- Orders are public: there is no encrypted mempool (§1.3).
- The model has no swap fee. Confirmed on a full read (2026-10-17): the only "fee" mentions in the paper are to transaction fee mechanism papers. The potential function is constant (Φ(x′, y′) = Φ(x, y)), so nothing accrues to liquidity providers.
- Rates are always Y paid per unit of X (Definition 1). Figure 1 sizes each order in X at r0: β = v for Buy(X), −v for Sell(X), −v/r0 for Buy(Y), v/r0 for Sell(Y). Step 3a puts every minority-side order in front of the dominant side; the boundary order is split.
- The paper gives no numerical worked example of the mechanism. Its only example (Appendix A) illustrates the preference ordering. The tests here therefore check Figure 1's rules and Theorem 3.1 directly.
- The scope is one pool. Cross-pool interaction, all-or-nothing orders and encrypted mempools are open problems (§1.3, §5).

**Empirical gap.** The paper is theory only and contains no on-chain measurement. This study supplies the measurement it leaves out.

**Follow-up by others:** Li, Shi, Zhang, "A Trilemma in AMM Mechanism Design", [arXiv 2605.27602](https://arxiv.org/abs/2605.27602) (May 2026; Ke Wu is not an author). Of incentive compatibility (IC), weak local efficiency (wLE: no unfilled demand from orders that could have executed directly against the pool) and uniform pricing (UP), any two are achievable but not all three. Chan–Wu–Shi's mechanism gives up UP. This is why the outreach must not call it a uniform-price batch auction, and it suggests a question: how much efficiency the measured blocks lose to the IC choice (the unfilled volume this study reports).

## 2. Wellman's angle

- Michael P. Wellman is Lynn A. Conway Collegiate Professor at UMich CSE and leads the [Strategic Reasoning Group](https://strategicreasoning.org/publications/).
- I found no blockchain, MEV or AMM work in his CV (July 2024) or the group's publication list. A 2025–26 DeFi workshop paper could still exist; Google Scholar was not searched.
- The direct hook is batch versus continuous markets:
  - Wah & Wellman, "Latency arbitrage in fragmented markets", Algorithmic Finance 2016 ([link](https://content.iospress.com/doi/10.3233/AF-160060)). It finds that frequent call markets eliminate latency arbitrage.
  - Wah, Hurd, Wellman, "Strategic market choice: frequent call markets vs. continuous double auctions" (AMMA 2015).
  - His [CFTC comment](https://comments.cftc.gov/Handlers/PdfHandler.ashx?id=25238) arguing for call markets.
- His method is agent-based simulation, such as PyMarketSim ([ICAIF 2024](https://strategicreasoning.org/wp-content/uploads/2024/10/MarketSim_ICAIF24.pdf)) and the spoofing work. A historical counterfactual replay is a natural first step toward that kind of simulation.
- I found no joint Ke Wu–Wellman paper, student or lab.
- **Rechecked 2026-10-17.** His 25 most recent arXiv papers (author query `au:Wellman_Michael`, newest Feb 2026) contain nothing on blockchains, MEV or AMMs. A web search also found none. The recent work is empirical game-theoretic analysis (EGTA): for example "Learning Bayesian Game Families, with Application to Mechanism Design" (Feb 2025), "Computing Perfect Bayesian Equilibria, with Application to Empirical Game-Theoretic Analysis" (Feb 2026) and an EGTA survey (2024). Note: "The Viability of Blockchain Markets under Discrete Clearing and Paid Priority" (arXiv 2605.17425) looks like his topic but is by Capponi, Cartea and Drissi.
- **Sharper hook for Wellman:** this study's main limit is that it replays the same orders and can't say how bots and traders would respond to the mechanism. Working out that response is an empirical game, which is his method.

## 3. Data access (tested 2026-10-17)

| Source | Status |
|---|---|
| `rpc.mevblocker.io` | Free. Historical `eth_getLogs` works in 1,000-block ranges (the agent saw requests split above 10k), and archive `eth_call` works. **Primary source.** |
| `eth.drpc.org` | Free. getLogs works in 100-block ranges, and archive `eth_call` works. Fallback. |
| `ethereum-rpc.publicnode.com` | Free. getLogs over 2,000 blocks returned 1,128 swaps on the USDC/WETH 0.05% pool. Archive calls need a token, and `debug_trace*` is not available. |
| Dune | Free plan is view-only. A one-time 14-day trial includes 2,500 credits. Use the trial in one sitting to validate against `dex_ethereum.sandwiches`. |
| The Graph (Uniswap subgraph) | Needs a key; 100k queries/month free. Gives no tx index, priority fee or builder. Not needed. |
| EigenPhi | Paid only since 2026-04-15 ([notice](https://eigenphi.substack.com/p/important-update-regarding-eigenphi)). |
| ZeroMEV | Dead; coverage ends around January 2025. |
| libMEV API | HTTP 522 on 2026-10-17. |
| Flashbots relay data API | Free. Gives the builder per block. |
| [Mempool Dumpster](https://github.com/flashbots/mempool-dumpster) | Free, CC-0, daily files. A victim missing from it was probably sent privately. |

## 4. Sandwich detection

Rules from the literature:

- **Qin, Zhou, Gervais**, S&P 2022 ([2101.05511](https://arxiv.org/abs/2101.05511)):
  - front-run, victim and back-run in one block, in that order;
  - the front-run and victim trade in one direction and the back-run in the other;
  - the same address sends both legs, or two addresses send them to the same contract;
  - the back-run sells 90–110% of what the front-run bought.
- **Torres et al.**, USENIX 2021 ([2102.03347](https://arxiv.org/abs/2102.03347)): token flows match within 1%. Their gas-price ordering rule is obsolete because of bundles.
- **Dune spellbook** ([macro](https://github.com/duneanalytics/spellbook/blob/main/dbt_subprojects/dex/macros/models/dex_sandwiches.sql)): same block, same pool and same `tx_from`, plus a victim. It has no amount check.
- **Chi et al. 2024** ([2405.17944](https://arxiv.org/abs/2405.17944)): multi-victim "burgers" (13.1%) and multi-transaction legs. Reported error is at most 2.4%.
- **Heimbach, Solmaz, Öz, Torres 2026** ([2609.28115](https://arxiv.org/abs/2609.28115)):
  - merge split legs;
  - one role per tx;
  - a persistent-bot filter, so that two-way high-frequency traders are not labelled sandwichers;
  - victim loss by exact counterfactual re-simulation.

**Rule this study uses.**

- Same block and same pool. The front-run and back-run go in opposite directions, with at least one swap between them in the front-run direction from a different sender.
- The attacker matches on the same EOA, or on the same bot contract with the amount within ±1%.
- Report results at two thresholds: Qin ±10% and strict ±1%.
- Count each victim separately.
- Known misses: cross-block sandwiches, multi-pool legs and legs that use different contracts. Report these as limits.

## 5. Loss measures

- **(a) Counterfactual loss (headline).** Re-execute the victim's exact input against the pool state without the front-run, keeping any other victims in order. Loss is the counterfactual output minus the actual output.
  - On v3, the Swap event carries `sqrtPriceX96`, `liquidity` and `tick` after the swap. The previous swap in the same pool therefore gives the pre-state, after applying any Mint or Burn in between.
  - If the swap crosses a tick, fetch `ticks()` and `liquidityNet` for that tick by archive `eth_call` at N−1.
  - Port `TickMath` and `SwapMath` to Python integers. **Gate:** the port must reproduce every observed swap exactly before any counterfactual is trusted.
- **(b) Attacker profit.** Back-run output minus front-run input, then net of gas. This is a lower bound on harm, because builders take most of the value.
- **(c) Slippage tolerance available to the attacker.** The no-attack output minus `amountOutMinimum` decoded from calldata (or `amountInMaximum` minus the no-attack input). This is the most a sandwich could take from that victim. Loss (a) divided by (c) is how much of the tolerance the attacker used. Only defined where the victim's calldata decodes.

## 6. Counterfactual for the batch design

- **Batch:** all swaps on the pool in one block, with r0 from the state at the start of the block.
- **Limit price:** decode it from router calldata (`amountOutMinimum` / `amountInMaximum`, plus `sqrtPriceLimitX96` where set). Uniswap limits bound the *average* price, while the paper's limit is *marginal*.
  - Main run: treat the average limit as marginal. This fills less and is conservative.
  - Sensitivity run: unlimited orders.
- **Universal Router:** decoding its commands is the hardest step. If a victim's limit cannot be decoded, use the executed price as a lower bound on its limit and flag the swap.
- **Phase 2:** maps onto v3 swap math with `sqrtPriceLimitX96` set to the order's limit. "Fill until the marginal price reaches the limit" is exactly what that price limit does.
- **Fees:** the paper has none. Run phase 1 both with and without the pool fee, and keep the fee in phase 2.
- **Randomness:** draw at least 200 random orderings of the dominant side and report the mean and 5–95% range.
- **Outputs:**
  1. The attacker's net under the mechanism. Theorem 3.1 predicts at most 0; any positive result means a bug or a broken assumption.
  2. Each victim's outcome under the mechanism, compared with (a) the no-attack counterfactual and (b) actual execution.
  3. **Share of the sandwich loss prevented** = (victim's mechanism outcome − actual outcome) / sandwich loss (a). It can exceed 100%, because phase 1 matching beats the status quo even without an attack. Report that excess separately, and do not count it as sandwich prevention.
  4. The unfilled amount caused by partial fills, which Uniswap would have filled completely or reverted.

## 7. Where sandwiches happen now

- **4-hour scan of all pools** (blocks 26,213,424–26,214,623, `data/probe-2026-10-17/`):
  - 52,396 swaps across 3,756 pools; 100 sandwiches passed the ±10% amount check.
  - **None** were on USDC/WETH (v2, v3 0.05%, v3 0.3%) or on WETH/USDT v3 0.05% and 0.3%.
  - Three were on WETH/USDT v3 0.01%.
  - The rest were on long-tail pools, mostly v4 and memecoin pools.
  - Two EOAs made 48% of the hits.
- **One-day scan of nine candidate pools:** see `docs/pool-selection.md`.
- **Correction (2026-10-18):** the four-hour probe did not separate v3 USDC/WETH 0.01%, and the nine-pool list left it out. A full scan of 7 October shows it is the busiest v3 pool and is sandwiched about as often as the study pool (`docs/pool-selection.md`, correction section). Sandwiches concentrate in 0.01% fee tiers, not just in long-tail pools.

**Sanity figures.** EigenPhi via [Cointelegraph (Dec 2025)](https://cointelegraph.com/research/exclusive-data-from-eigenphi-reveals-that-sandwich-attacks-on-ethereum-have-waned) reports:

- about $60M a year in losses, Nov 2024 to Oct 2025;
- monthly extraction falling from about $10M to about $2.5M;
- about 70% of attacks by jaredfromsubway.

The article does not state its method. For private-flow sandwiches, see Mancino & Rezzoli ([2512.17602](https://arxiv.org/abs/2512.17602)) and Adams et al. ([2309.13648](https://arxiv.org/abs/2309.13648)).
