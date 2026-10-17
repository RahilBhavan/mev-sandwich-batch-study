# MEV sandwich study: one Uniswap pool, one week, and per-block batch clearing

This study measures sandwich attacks on one Uniswap pool over one week. It estimates what the victims lost, then replays each block through the two-phase swap mechanism of Chan, Wu & Shi, "Mechanism Design for Automated Market Makers" (AFT 2025, [arXiv 2402.09357](https://arxiv.org/abs/2402.09357)) to estimate how much of that loss the mechanism would have prevented.

Status (2026-10-17): research and pool selection. No results yet.

- `docs/research.md`: the paper's mechanism, detection rules, loss measures and data access, all sourced
- `docs/plan.md`: questions, outputs, a 10-day schedule and limits
- `docs/pool-selection.md`: the candidate-pool scan and the chosen pool
- `scripts/scan_pools.py`: counts same-block sandwiches on candidate pools from a free public RPC
- `scripts/probe_all_pools.py`: 4-hour exploratory scan of all v2/v3/v4 pools

The `data/` and `references/` folders are local only and are not tracked in git.
