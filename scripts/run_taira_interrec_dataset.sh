#!/usr/bin/env bash
# Run TAIRA on one InterRec-aligned dataset (data already under TAIRA/data/<dataset>/).
#
# Usage:
#   bash scripts/run_taira_interrec_dataset.sh yelp
#   bash scripts/run_taira_interrec_dataset.sh movielens
#   bash scripts/run_taira_interrec_dataset.sh amazon_book
#   bash scripts/run_taira_interrec_dataset.sh lastfm
#
# Prereq: python3 scripts/convert_interrec_to_taira.py --dataset <name>
#
set -euo pipefail
set -o pipefail

DATASET="${1:?usage: $0 <lastfm|yelp|movielens|amazon_book>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TAIRA_DIR="$REPO_ROOT/TAIRA"
SCRIPTS_DIR="$SCRIPT_DIR"
LOG_BASE="$REPO_ROOT/results"
mkdir -p "$LOG_BASE/metrics"

CFG="$TAIRA_DIR/system_config.yaml"
if [ ! -f "$CFG" ]; then
  echo "Missing $CFG"
  exit 1
fi

# DOMAIN: "lastfm"  → requested dataset
sed -i "s/^DOMAIN:.*/DOMAIN: \"${DATASET}\"/" "$CFG"

cd "$TAIRA_DIR"

echo "[$(date)] TAIRA dataset=${DATASET} (QUERY_NUMBER from system_config.yaml)"

for SEED in 0 1 2; do
  echo ""
  echo "========== seed=${SEED} =========="
  PYTHONHASHSEED="$SEED" python main.py 2>&1 | tee "${LOG_BASE}/${DATASET}_seed${SEED}_stdout.log"

  LATEST_LOG_DIR="$(ls -td "$TAIRA_DIR/data/$DATASET/logs"/TAIRA-* 2>/dev/null | head -1 || true)"
  LATEST_CSV="$(ls -t "$LATEST_LOG_DIR"/*.csv 2>/dev/null | head -1 || true)"
  if [ -n "$LATEST_CSV" ]; then
    python3 "$SCRIPTS_DIR/parse_taira_metrics.py" \
      "$LATEST_CSV" \
      "$LOG_BASE/metrics/run_${DATASET}_seed${SEED}.json" \
      "$SEED"
    echo "[$(date)] metrics → $LOG_BASE/metrics/run_${DATASET}_seed${SEED}.json"
  else
    echo "[warn] no result CSV for seed=$SEED"
  fi
done

echo ""
echo "[$(date)] Done all seeds for ${DATASET}. Aggregating with collect_taira_results.py …"
cd "$(dirname "$SCRIPTS_DIR")"
python3 "$SCRIPTS_DIR/collect_taira_results.py" || true
