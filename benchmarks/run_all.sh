#!/bin/bash
# Run every experiment in sequence (one at a time so timings do not interfere).
cd "$(dirname "$0")"
export PYTHONPATH=../src
mkdir -p ../results
for b in bench_counts bench_sorting bench_lookup bench_retrieval; do
  python -u $b.py > ../results/log_${b#bench_}.txt 2>&1
done
echo finished > ../results/ALL_DONE
