#!/usr/bin/env bash
# run_lastfm_seeds.sh
# Run TAIRA on LastFM dataset for 3 seeds sequentially

set -e
TAIRA_DIR="/root/main_table_experiments/baselines/taira_official/TAIRA"
SCRIPTS_DIR="/root/main_table_experiments/baselines/taira_official/scripts"
LOG_BASE="/root/main_table_experiments/baselines/taira_official/results"

mkdir -p "$LOG_BASE"

echo "[$(date)] Starting TAIRA lastfm experiment - 3 seeds"
echo "TAIRA_DIR: $TAIRA_DIR"

cd "$TAIRA_DIR"

for SEED in 0 1 2; do
    echo ""
    echo "============================================="
    echo "[$(date)] Running seed=$SEED"
    echo "============================================="

    PYTHONHASHSEED=$SEED python main.py 2>&1 | tee "$LOG_BASE/lastfm_seed${SEED}_stdout.log"

    echo "[$(date)] Seed $SEED done."

    # Parse results for this seed
    LATEST_LOG_DIR=$(ls -td "$TAIRA_DIR/data/lastfm/logs"/TAIRA-* | head -1)
    LATEST_CSV=$(ls -t "$LATEST_LOG_DIR"/*.csv 2>/dev/null | head -1)

    if [ -n "$LATEST_CSV" ]; then
        echo "[$(date)] Parsing results from: $LATEST_CSV"
        mkdir -p "$LOG_BASE/metrics"
        python3 "$SCRIPTS_DIR/parse_taira_metrics.py" \
            "$LATEST_CSV" \
            "$LOG_BASE/metrics/run_lastfm_seed${SEED}.json" \
            "$SEED"
        echo "[$(date)] Seed $SEED metrics saved."
    else
        echo "[ERROR] No CSV found in $LATEST_LOG_DIR"
    fi
done


echo ""
echo "[$(date)] Seed 0 done for lastfm. Run other datasets with:"
echo "  DOMAIN=yelp bash .../run_taira_one_dataset.sh"
echo "Or wait for all lastfm seeds to finish."
