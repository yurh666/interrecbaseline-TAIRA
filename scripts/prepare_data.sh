#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAIRA_DIR="${ROOT_DIR}/TAIRA"
DOMAIN="${1:-amazon_music}"
LOG_FILE="${ROOT_DIR}/results/raw_logs/prepare_data_${DOMAIN}.log"

mkdir -p "${ROOT_DIR}/results/raw_logs" "${TAIRA_DIR}/data/${DOMAIN}"

echo "Preparing TAIRA data for domain=${DOMAIN}" | tee "${LOG_FILE}"

if [[ -f "${TAIRA_DIR}/data/prepare.py" ]]; then
  (
    cd "${TAIRA_DIR}"
    python data/prepare.py --domain "${DOMAIN}"
  ) 2>&1 | tee -a "${LOG_FILE}"
elif [[ -f "${TAIRA_DIR}/README.md" ]]; then
  {
    echo "No data/prepare.py was found."
    echo "Follow the official README data instructions manually, then place files under:"
    echo "  ${TAIRA_DIR}/data/${DOMAIN}/"
    echo "This script intentionally does not fabricate TAIRA data."
  } | tee -a "${LOG_FILE}"
else
  echo "ERROR: TAIRA README/code not found under ${TAIRA_DIR}" | tee -a "${LOG_FILE}"
  exit 2
fi

echo "Data preparation step finished. Verify official dataset files before running experiments." | tee -a "${LOG_FILE}"
