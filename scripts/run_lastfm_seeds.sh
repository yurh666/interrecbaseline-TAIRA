#!/usr/bin/env bash
# run_lastfm_seeds.sh
# Run TAIRA on LastFM for one or more seeds (default 0 1 2).
# Uses main_resume.py + stable CSV under results/checkpoints/ so SSH/API 中断后可续跑。
#
# Examples:
#   bash scripts/run_lastfm_seeds.sh              # seeds 0 1 2
#   bash scripts/run_lastfm_seeds.sh 2            # only seed 2
#   TAIRA_FORCE_RERUN=1 bash scripts/run_lastfm_seeds.sh   # 忽略「已完成」跳过逻辑，重算
#
set -euo pipefail

export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TAIRA_DIR="$REPO_ROOT/TAIRA"
SCRIPTS_DIR="$SCRIPT_DIR"
LOG_BASE="$REPO_ROOT/results"

mkdir -p "$LOG_BASE/metrics" "$LOG_BASE/checkpoints/lastfm"

if [[ $# -gt 0 ]]; then
  SEEDS=( "$@" )
else
  # shellcheck disable=SC2206
  SEEDS=( ${TAIRA_LASTFM_SEEDS:-0 1 2} )
fi

PY="${TAIRA_PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python

echo "[$(date)] Starting TAIRA lastfm — seeds: ${SEEDS[*]} (checkpointed via main_resume.py)"
echo "TAIRA_DIR: $TAIRA_DIR"

CFG="$TAIRA_DIR/system_config.yaml"
sed -i 's/^DOMAIN:.*/DOMAIN: "lastfm"/' "$CFG"
echo "[$(date)] Patched DOMAIN=lastfm in $CFG"

cd "$TAIRA_DIR"

for SEED in "${SEEDS[@]}"; do
    echo ""
    echo "============================================="
    echo "[$(date)] Running seed=$SEED"
    echo "============================================="

    CKPT_CSV="$LOG_BASE/checkpoints/lastfm/seed_${SEED}/result-TAIRA.csv"
    mkdir -p "$(dirname "$CKPT_CSV")"

    if [[ "${TAIRA_FORCE_RERUN:-}" != "1" ]] && \
       [[ -f "$LOG_BASE/metrics/run_lastfm_seed${SEED}.json" ]] && \
       "$PY" "$SCRIPTS_DIR/check_checkpoint_complete.py" lastfm "$CKPT_CSV"; then
      echo "[$(date)] skip lastfm seed=${SEED} (checkpoint + metrics already complete)"
      continue
    fi

    PYTHONHASHSEED=$SEED "$PY" main_resume.py --resume-csv "$CKPT_CSV" 2>&1 | tee "$LOG_BASE/lastfm_seed${SEED}_stdout.log"

    echo "[$(date)] Parsing checkpoint: $CKPT_CSV"
    "$PY" "$SCRIPTS_DIR/parse_taira_metrics.py" \
        "$CKPT_CSV" \
        "$LOG_BASE/metrics/run_lastfm_seed${SEED}.json" \
        "$SEED"
    echo "[$(date)] Seed $SEED metrics saved."
done

echo ""
echo "[$(date)] LastFM seeds finished: ${SEEDS[*]}"
