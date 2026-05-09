#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAIRA_DIR="${ROOT_DIR}/TAIRA"
DOMAIN="${1:-amazon_music}"
SEED="${2:-0}"
LOG_FILE="${ROOT_DIR}/results/raw_logs/eval_${DOMAIN}_seed${SEED}.log"

mkdir -p "${ROOT_DIR}/results/raw_logs" "${ROOT_DIR}/results/metrics"

if [[ -f "${TAIRA_DIR}/eval.py" ]]; then
  (
    cd "${TAIRA_DIR}"
    python eval.py --domain "${DOMAIN}" --seed "${SEED}"
  ) 2>&1 | tee "${LOG_FILE}"
elif [[ -f "${TAIRA_DIR}/main.py" ]]; then
  echo "No standalone eval.py found; parse metrics from the main run log instead." | tee "${LOG_FILE}"
  python "${ROOT_DIR}/scripts/parse_taira_metrics.py" \
    "${ROOT_DIR}/results/raw_logs/run_${DOMAIN}_seed${SEED}.log" \
    "${ROOT_DIR}/results/metrics/run_${DOMAIN}_seed${SEED}.json"
else
  echo "ERROR: Official TAIRA eval/main entrypoint is unavailable." | tee "${LOG_FILE}"
  exit 2
fi
