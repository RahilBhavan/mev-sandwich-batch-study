# Multi-pool, four-week detection

This file records the 2026-10-25 extension of the study from one pool and one week to three Uniswap v3 pools and four weeks. It covers detection only. Numbers come from `results/multi-pool/summary.json`; the table is `results/multi-pool/table.md`.

## Question and scope

Does the sandwich count from the original week (WETH/USDT 0.01%, 5-11 Oct 2026) hold up across other busy pools and other weeks, using the same detector?

Run: 3 pools x 4 weeks = 12 pool-weeks, 1,136,585 swaps. The detector is `mev/detect.py` with the window the main analysis uses (`detect.QIN`, back-run input 90-110% of front-run output; the strict ±1% count is reported beside it). Nothing in the detector was changed or retuned.

## Choice of pools and weeks

- **Pool rule.** The three Uniswap v3 pools with the most swaps on 7 Oct 2026 (blocks 26,136,840-26,144,039), from the all-pool scan in `scripts/probe_all_pools.py`. That scan counted 24,012 swaps in USDC/WETH 0.01%, 10,150 in WETH/USDT 0.01% and 7,885 in USDC/WETH 0.05%. The fourth, `0x894d4e6d3d2abc64fc0de0e4e2ea63a93bc9c520`, had 3,590 and was not run.
- **Why v3 only.** The detector's swap decoding and the repository's exact swap math are for v3. Busy v2 and v4 pools exist (`docs/pool-selection.md`) but were not run.
- **One reference day.** The rule uses a single day, inside the original week. A different day could rank the pools differently.
- **Weeks.** Four consecutive Monday-to-Sunday UTC weeks starting 14, 21 and 28 September and 5 October 2026. Block ranges come from a binary search on block timestamps (`block_range` in `scripts/multi_scan.py`). The 5 October range matches `mev/pool.py`, and the weeks join with no gap (for example 26,122,439 then 26,122,440).

## Data access

Free public JSON-RPC was enough. No key, archive state or local data was needed, because detection reads only Swap logs and each transaction's sender and target.

- **Endpoint.** `rpc.mevblocker.io`, with `eth.drpc.org` as the fallback in `mev/rpc.py`.
- **`eth_getLogs` limit.** Observed on 2026-10-25: mevblocker answers "query returned more than 10000 results" for a 10,000-block range on WETH/USDT 0.01% (about 1,400 to 1,800 swaps per 1,000 blocks in these weeks). The scan therefore pulls 1,000-block chunks. USDC/WETH 0.01% has about 3,000 swaps per 1,000 blocks, which also fits. eth.drpc.org returned HTTP 400 for the same 10,000-block query.
- **Transaction lookups are the cost.** The scan fetches sender and target with `eth_getTransactionByHash`. One USDC/WETH 0.01% week needed 71,081 lookups and took tens of minutes. The whole 12 pool-week run took hours, with HTTP 429 and 504 retries, run as two processes.
- **Block filter.** To cut lookups, the scan skips blocks that cannot hold a sandwich, meaning blocks with no front-run leg followed by a same-direction victim leg and then an opposite-direction leg (`keep_block`). This does not change results. On the original week's local data, the detector gives the same 236 sandwiches with and without the filter (`tests/test_multi_scan.py` repeats the check on 3,000 random blocks).

## Checks that the scan reproduces the study

- The original pool and week (WETH/USDT 0.01%, 5-11 Oct) re-run live through `scripts/multi_scan.py` gives 70,669 swaps, 236 sandwiches, 193 strict, 244 victims and 23 attacker addresses. These match `results/summary.json`.
- Its swap count (70,669) and transaction count (69,028) match the original ingest.

## Results

| Pool | Week (UTC, Monday) | Swaps | Sandwiches | Strict ±1% | Victims | Attacker addresses | Top attacker share |
|---|---|---:|---:|---:|---:|---:|---:|
| USDC/WETH 0.01% | 2026-09-14 | 147,100 | 218 | 162 | 223 | 25 | 24% |
| USDC/WETH 0.01% | 2026-09-21 | 150,606 | 130 | 90 | 139 | 22 | 32% |
| USDC/WETH 0.01% | 2026-09-28 | 158,585 | 103 | 81 | 108 | 20 | 30% |
| USDC/WETH 0.01% | 2026-10-05 | 157,335 | 131 | 99 | 136 | 17 | 30% |
| **USDC/WETH 0.01% total** | 4 weeks | **613,626** | **582** | **432** | **606** | | |
| WETH/USDT 0.01% | 2026-09-14 | 90,003 | 324 | 251 | 340 | 30 | 37% |
| WETH/USDT 0.01% | 2026-09-21 | 75,075 | 260 | 213 | 277 | 37 | 35% |
| WETH/USDT 0.01% | 2026-09-28 | 72,236 | 193 | 152 | 199 | 23 | 39% |
| WETH/USDT 0.01% | 2026-10-05 | 70,669 | 236 | 193 | 244 | 23 | 41% |
| **WETH/USDT 0.01% total** | 4 weeks | **307,983** | **1013** | **809** | **1060** | | |
| USDC/WETH 0.05% | 2026-09-14 | 61,512 | 0 | 0 | 0 | 0 | n/a |
| USDC/WETH 0.05% | 2026-09-21 | 47,016 | 3 | 3 | 7 | 3 | 33% |
| USDC/WETH 0.05% | 2026-09-28 | 55,419 | 4 | 2 | 4 | 4 | 25% |
| USDC/WETH 0.05% | 2026-10-05 | 51,029 | 5 | 5 | 5 | 3 | 60% |
| **USDC/WETH 0.05% total** | 4 weeks | **214,976** | **12** | **10** | **16** | | |

- "Sandwiches", "Strict" and "Victims" are the detector's counts. "Attacker addresses" counts distinct sending addresses of the front-runs. "Top attacker share" is the most frequent address's share of that pool-week's sandwiches.
- Over the four weeks, the detector flagged 1,013 sandwiches in 307,983 WETH/USDT 0.01% swaps (0.33%), 582 in 613,626 USDC/WETH 0.01% swaps (0.09%) and 12 in 214,976 USDC/WETH 0.05% swaps (0.006%).
- Both 0.01% pools are sandwiched every week and the 0.05% pool almost never. This repeats the fee-tier pattern in `docs/pool-selection.md` on four weeks of data. The data do not test why.
- Weekly counts fall from the first week to the later ones in both 0.01% pools (WETH/USDT 324, 260, 193, 236; USDC/WETH 218, 130, 103, 131). Four weeks do not show a trend.
- `results/multi-pool/sandwiches.csv` lists every detection with its block, transactions, attacker addresses and ratio.

## Limits that carry over

- **Precision.** The only precision review is the original 30-hit review of WETH/USDT 0.01% for 5-11 Oct (25 sandwiches, 3 where the attacker lost money, 2 routed through other pools, 0 false positives; `results/precision-review.md`). No hit from the other 11 pool-weeks has been reviewed. The new pools have a different mix of routers and bots, so the 30-of-30 result does not transfer. A human Etherscan check is still pending: `results/spot-check/` holds a blind 10-candidate sample drawn from these detections.
- **No loss, no mechanism result.** Victim loss, attacker profit and the two-phase counterfactual need the exact replay from archive state at each week's start. That was not run for the new pool-weeks, so this extension reports counts only. The headline $12,387 and 75% figures still cover only the original pool and week.
- **Detector scope.** Same-block, single-pool sandwiches only, as in `docs/methods.md`.
- **Earlier control count differs.** `docs/pool-selection.md` records 13 sandwiches for USDC/WETH 0.05% in 5-11 Oct from the quicker `scripts/scan_pools.py` detector. This scan, which uses the full detector, finds 5 in the same 51,029 swaps. The two detectors differ, and the 13 was not re-derived here.
- **One sample per pool.** Four consecutive weeks are not a year, and only three pools were run.

## Reproduce

```bash
.venv/bin/python scripts/multi_scan.py ~/scratch/mev-cache results/multi-pool
.venv/bin/python scripts/spot_check.py results/multi-pool/sandwiches.csv results/spot-check
```

The first command needs network access and takes hours; a rerun with the cache directory present makes no new RPC calls. `--table-only` rebuilds `table.md` from `summary.json` offline.
