# MEV sandwich study: one Uniswap pool, one week, and per-block batch clearing

This study measures sandwich attacks on one Uniswap pool over one week. It estimates what the victims lost, then replays each block through the two-phase swap mechanism of Chan, Wu & Shi, "Mechanism Design for Automated Market Makers" (AFT 2025, [arXiv 2402.09357](https://arxiv.org/abs/2402.09357)) to estimate how much of that loss the mechanism would have prevented.

## Result (5–11 October 2026, Uniswap v3 WETH/USDT 0.01%)

- **Sandwiches and losses.** 70,669 swaps. 236 sandwiches hit 244 victims, who lost **$12,387** against what they would have received with no front-run. Attackers grossed $8,713 and paid at least 65% of it as gas.
- **Slippage taken.** Where the victim's minimum output could be decoded, attackers took 98% of the slippage tolerance.
- **The attack under the mechanism.** No sandwich makes money for its attacker in any run.
- **The victims.** With the same orders replayed, victims keep 75% of their loss on average across 200 random tie-breaks (52–99% across variants). If attackers stop, they keep essentially all of it.

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

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python pyarrow matplotlib pytest
scripts/run_all.sh
```

`data/`, `references/` and `outreach/` are local only and are not tracked in git.
