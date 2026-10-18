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
