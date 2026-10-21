# MEV sandwich study: one Uniswap pool, one week, and per-block two-phase clearing

Measures sandwich attacks on the busiest WETH/USDT Uniswap v3 pool over one week, estimates what the victims lost, then replays each block through the per-block, two-phase, arbitrage-resilient mechanism of Chan, Wu & Shi, "Mechanism Design for Automated Market Makers" (AFT 2025, [arXiv 2402.09357](https://arxiv.org/abs/2402.09357)) to estimate how much of that loss the mechanism would have prevented.

## Results (5–11 October 2026, Uniswap v3 WETH/USDT 0.01%)

- **Sandwiches and losses.** 70,669 swaps. 236 sandwiches hit 244 victims, who lost **$12,387** against what they would have received with no front-run. Attackers grossed $8,713 and paid at least 50% of it as gas.
- **Slippage taken.** Where the victim's minimum output could be decoded, attackers took 98% of the slippage tolerance.
- **The attack under the mechanism.** No sandwich makes money for its attacker in any run.
- **The victims.** With the same orders replayed, victims keep 75% of their loss on average across 200 random tie-breaks (52–99% across variants). If attackers stop, they keep essentially all of it.
- **Exact replay gate.** The Python port of Uniswap v3's integer swap math reproduces all 70,669 swaps bit-exactly before any counterfactual is computed.

**How it works:** `scripts/ingest.py` pulls the week's swaps over JSON-RPC, `replay.py` checks exact v3 replay, `mev/detect.py` finds sandwiches, and `mev/mechanism.py` re-clears each block under the paper's two-phase rules; `scripts/run_all.sh` runs the whole pipeline.

**Run the tests:** `uv venv .venv && uv pip install --python .venv/bin/python pyarrow matplotlib pytest && .venv/bin/python -m pytest -q` (19 tests)

Further results:

- **Memecoin extension (SIMD/WETH 0.01%, same week).** 240 sandwiches, $1,330 lost, 95% of it by one automated buyer. No attack pays under the mechanism, and victims keep 73% on average with the same orders (`results/simd-weth/`).
- **Detection cross-check.** Dune's spellbook rule, re-implemented locally, confirms 99.6% and 100% of the sandwich blocks in the two pools (`results/dune-rule-replication.md`).

![Cumulative victim loss](results/figure.png)

Read `docs/methods.md` first. Tables are in `results/tables.md`.

## Layout

- `mev/`
  - `v3.py`: exact Uniswap v3 swap math
  - `mechanism.py`: the paper's Figure 1
  - `detect.py`: sandwich detection
  - `calldata.py`: router limit decoding
  - `rpc.py`, `data.py`, `pool.py`: data access and pool constants
- `scripts/`
  - `ingest.py`, then `replay.py` (gate: 100% exact)
  - `analyze.py`, then `inspect_hits.py`, then `report.py`
  - `run_all.sh` runs everything
  - `compare_dune.py`: cross-check against a Dune export of `docs/dune/sandwiches.sql`
  - `scan_pools.py`: candidate-pool and control counts
- `tests/`: v3 math, the detector, and the mechanism's rules and Theorem 3.1
- `docs/`
  - `research.md`: sources
  - `plan.md`: plan and status
  - `pool-selection.md`: pool choice and frozen week
  - `methods.md`: methods note
- `results/`: CSVs, `summary.json`, tables, figure and its brief, and precision evidence
- `textbook/`: a self-contained study guide (`index.html`) that teaches everything needed to explain and defend the study; built by `build.py` from the results and the tested code. Plan in `PLAN.md`, checks in `CHECKS.md`

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python pyarrow matplotlib pytest
scripts/run_all.sh
```

`data/`, `references/` and `outreach/` are local only and are not tracked in git.
