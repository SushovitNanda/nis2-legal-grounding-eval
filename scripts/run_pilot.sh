#!/usr/bin/env bash
# Run from the repository root:  bash scripts/run_pilot.sh
# The pilot of 14 Nov 2026 (results/pilot/) used provisional question wording and the judge configured then.
# S6 - pilot: batch 1 (10 questions), all models, core conditions, 1 repetition.
set -euo pipefail
python -m nis2eval validate
python -m nis2eval run   --run pilot --batch 1 --reps 1 --conditions C0,C1,C2
python -m nis2eval score --run pilot
python -m nis2eval analyze --run pilot
echo "Sanity check (T5): in results/pilot/analysis/summary.md, C1 coverage should not be below C0."
