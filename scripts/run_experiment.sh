#!/bin/bash
# taira_official/scripts/run_experiment.sh
# Usage: bash run_experiment.sh [domain] [seed]
# Example: bash run_experiment.sh amazon_music 0
set -e

DOMAIN=${1:-amazon_music}
SEED=${2:-0}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
TAIRA_DIR="$BASE_DIR/TAIRA"

echo "========================================"
echo "TAIRA Experiment: domain=$DOMAIN seed=$SEED"
echo "Started: $(date)"
echo "========================================"

LOG_FILE="$BASE_DIR/results/raw_logs/run_${DOMAIN}_seed${SEED}.log"
mkdir -p "$BASE_DIR/results/raw_logs" "$BASE_DIR/results/metrics"

# Set reproducibility env vars
export PYTHONHASHSEED=$SEED
export OPENAI_API_KEY="${OPENAI_API_KEY:-$(grep OPENAI_API_KEY $TAIRA_DIR/system_config.yaml | awk '{print $2}' | tr -d '"')}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-$(grep OPENAI_BASE_URL $TAIRA_DIR/system_config.yaml | awk '{print $2}' | tr -d '"')}"

# Activate conda env
source /root/miniconda3/etc/profile.d/conda.sh
conda activate taira

cd "$TAIRA_DIR"
python main.py 2>&1 | tee "$LOG_FILE"

echo "========================================"
echo "Finished: $(date)"
echo "Log saved to: $LOG_FILE"
echo "========================================"
