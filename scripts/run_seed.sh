#!/usr/bin/env bash
# run_seed.sh <seed>
# Runs one TAIRA seed (always fresh run for reproducibility).
# Results are written per-query to CSV; if interrupted, re-run with
#   bash run_seed.sh <seed> --resume <csv_path>
# to continue from where it left off.
set -euo pipefail

SEED="${1:-0}"
RESUME_CSV="${3:-}"   # Optional: pass --resume <path> as arg 2/3
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAIRA_DIR="${ROOT_DIR}/TAIRA"
LOG_DIR="${ROOT_DIR}/results/raw_logs"
mkdir -p "${LOG_DIR}"

RUN_LOG="${LOG_DIR}/seed${SEED}_run.log"

echo "[seed${SEED}] Starting at $(date)" | tee -a "${RUN_LOG}"
export PYTHONHASHSEED="${SEED}"

RESUME_ARG=""
if [[ "${2:-}" == "--resume" && -n "${RESUME_CSV}" ]]; then
    echo "[seed${SEED}] Resuming from: ${RESUME_CSV}" | tee -a "${RUN_LOG}"
    RESUME_ARG="--resume-csv"
fi

(
    cd "${TAIRA_DIR}"
    if [[ -n "${RESUME_ARG}" ]]; then
        python main_resume.py "${RESUME_ARG}" "${RESUME_CSV}"
    else
        python main_resume.py
    fi
) 2>&1 | tee -a "${RUN_LOG}"

echo "[seed${SEED}] Finished at $(date)" | tee -a "${RUN_LOG}"
