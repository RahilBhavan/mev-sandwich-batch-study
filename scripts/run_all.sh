#!/usr/bin/env bash
# Reproduce every result from the block range in mev/pool.py. Network access to a free archive RPC is required
# for ingest and inspect_hits; the rest is offline. Takes about an hour, mostly downloading transactions.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
$PY -m pytest -q tests
$PY scripts/ingest.py data/week
$PY scripts/replay.py data/week          # gate: must print matched=100%
$PY scripts/analyze.py data/week results
$PY scripts/inspect_hits.py data/week results
$PY scripts/report.py results
$PY scripts/dune_rule.py data/week results/dune-rule-replication.csv
$PY scripts/compare_dune.py results/dune-rule-replication.csv results

# memecoin extension: same pipeline on SIMD/WETH 0.01% (prices WETH from data/week, so run after the main pool)
export STUDY_POOL=simd-weth
$PY scripts/ingest.py data/simd-week
$PY scripts/replay.py data/simd-week
$PY scripts/analyze.py data/simd-week results/simd-weth
$PY scripts/inspect_hits.py data/simd-week results/simd-weth
$PY scripts/report.py results/simd-weth
$PY scripts/dune_rule.py data/simd-week results/simd-weth/dune-rule-replication.csv
unset STUDY_POOL
$PY textbook/build.py
