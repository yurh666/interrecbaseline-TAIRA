#!/bin/bash
# taira_official/scripts/run_all.sh
# Runs TAIRA for 3 seeds sequentially in a tmux session.
# Usage: bash run_all.sh [domain]
# Example: bash run_all.sh amazon_music
set -e

DOMAIN=${1:-amazon_music}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for SEED in 0 1 2; do
    echo "===== Seed $SEED ====="
    bash "$SCRIPT_DIR/run_experiment.sh" "$DOMAIN" "$SEED"
    echo "Seed $SEED done."
    sleep 5
done

echo "All seeds complete for domain=$DOMAIN"
