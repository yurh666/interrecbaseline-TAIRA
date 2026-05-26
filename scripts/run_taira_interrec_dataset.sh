#!/usr/bin/env bash
# Run TAIRA on one InterRec-aligned dataset (data already under TAIRA/data/<dataset>/).
# Uses main_resume.py + results/checkpoints/<dataset>/seed_*/result-TAIRA.csv 支持断点续跑。
#
# Usage:
#   bash scripts/run_taira_interrec_dataset.sh yelp
#   TAIRA_FORCE_RERUN=1 bash scripts/run_taira_interrec_dataset.sh movielens
#
set -euo pipefail
set -o pipefail

export PYTHONUNBUFFERED=1

DATASET="${1:?usage: $0 <lastfm|yelp|movielens|amazon_book>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$REPO_ROOT/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ROOT/.env.local"
  set +a
  echo "[$(date)] Loaded $REPO_ROOT/.env.local (OPENAI_* 等)"
fi

TAIRA_DIR="$REPO_ROOT/TAIRA"
SCRIPTS_DIR="$SCRIPT_DIR"
LOG_BASE="$REPO_ROOT/results"
mkdir -p "$LOG_BASE/metrics" "$LOG_BASE/checkpoints/$DATASET"

CFG="$TAIRA_DIR/system_config.yaml"
if [ ! -f "$CFG" ]; then
  echo "Missing $CFG"
  exit 1
fi

sed -i "s/^DOMAIN:.*/DOMAIN: \"${DATASET}\"/" "$CFG"

cd "$TAIRA_DIR"

PY="${TAIRA_PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python

echo "[$(date)] TAIRA dataset=${DATASET} (QUERY_NUMBER from system_config.yaml; checkpoints under results/checkpoints/${DATASET}/)"

for SEED in 0 1 2; do
  echo ""
  echo "========== seed=${SEED} =========="

  CKPT_CSV="$LOG_BASE/checkpoints/${DATASET}/seed_${SEED}/result-TAIRA.csv"
  mkdir -p "$(dirname "$CKPT_CSV")"

  if [[ "${TAIRA_FORCE_RERUN:-}" != "1" ]] && \
     [[ -f "$LOG_BASE/metrics/run_${DATASET}_seed${SEED}.json" ]] && \
     "$PY" "$SCRIPTS_DIR/check_checkpoint_complete.py" "$DATASET" "$CKPT_CSV"; then
    echo "[$(date)] skip ${DATASET} seed=${SEED} (checkpoint + metrics already complete)"
    continue
  fi

  PYTHONHASHSEED="$SEED" "$PY" main_resume.py --resume-csv "$CKPT_CSV" 2>&1 | tee "${LOG_BASE}/${DATASET}_seed${SEED}_stdout.log"

  echo "[$(date)] parse metrics ← $CKPT_CSV"
  "$PY" "$SCRIPTS_DIR/parse_taira_metrics.py" \
    "$CKPT_CSV" \
    "$LOG_BASE/metrics/run_${DATASET}_seed${SEED}.json" \
    "$SEED"
  echo "[$(date)] metrics → $LOG_BASE/metrics/run_${DATASET}_seed${SEED}.json"
done

echo ""
echo "[$(date)] Done all seeds for ${DATASET}. Aggregating with collect_taira_results.py …"
cd "$REPO_ROOT"
"$PY" "$SCRIPTS_DIR/collect_taira_results.py" || true
