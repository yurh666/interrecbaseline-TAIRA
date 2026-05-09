#!/usr/bin/env bash
# run_lastfm_seeds.sh
# Run TAIRA on LastFM for one or more seeds (default 0 1 2).
#
# Examples:
#   bash scripts/run_lastfm_seeds.sh              # seeds 0 1 2
#   bash scripts/run_lastfm_seeds.sh 2            # only seed 2 (新机器续跑)
#   bash scripts/run_lastfm_seeds.sh 0 1          # seeds 0 and 1
#   TAIRA_LASTFM_SEEDS="0 1" bash scripts/run_lastfm_seeds.sh   # 不在本机跑 seed2
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TAIRA_DIR="$REPO_ROOT/TAIRA"
SCRIPTS_DIR="$SCRIPT_DIR"
LOG_BASE="$REPO_ROOT/results"

mkdir -p "$LOG_BASE/metrics"

if [[ $# -gt 0 ]]; then
  SEEDS=( "$@" )
else
  # shellcheck disable=SC2206
  SEEDS=( ${TAIRA_LASTFM_SEEDS:-0 1 2} )
fi

echo "[$(date)] Starting TAIRA lastfm — seeds: ${SEEDS[*]}"
echo "TAIRA_DIR: $TAIRA_DIR"

cd "$TAIRA_DIR"

for SEED in "${SEEDS[@]}"; do
    echo ""
    echo "============================================="
    echo "[$(date)] Running seed=$SEED"
    echo "============================================="

    PYTHONHASHSEED=$SEED python main.py 2>&1 | tee "$LOG_BASE/lastfm_seed${SEED}_stdout.log"

    echo "[$(date)] Seed $SEED done."

    LATEST_LOG_DIR=$(ls -td "$TAIRA_DIR/data/lastfm/logs"/TAIRA-* | head -1)
    LATEST_CSV=$(ls -t "$LATEST_LOG_DIR"/*.csv 2>/dev/null | head -1)

    if [[ -n "$LATEST_CSV" ]]; then
        echo "[$(date)] Parsing results from: $LATEST_CSV"
        PY=python3
        command -v python3 >/dev/null 2>&1 || PY=python
        "$PY" "$SCRIPTS_DIR/parse_taira_metrics.py" \
            "$LATEST_CSV" \
            "$LOG_BASE/metrics/run_lastfm_seed${SEED}.json" \
            "$SEED"
        echo "[$(date)] Seed $SEED metrics saved."
    else
        echo "[ERROR] No CSV found in $LATEST_LOG_DIR"
    fi
done

echo ""
echo "[$(date)] LastFM seeds finished: ${SEEDS[*]}"
