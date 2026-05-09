#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAIRA_DIR="${ROOT_DIR}/TAIRA"
ENV_NAME="${TAIRA_ENV_NAME:-taira}"
PYTHON_VERSION="${TAIRA_PYTHON_VERSION:-3.12.7}"
CONDA_PKGS_DIRS="${TAIRA_CONDA_PKGS_DIRS:-/tmp/conda_pkgs_taira}"

mkdir -p "${ROOT_DIR}/results/raw_logs"

if [[ ! -f "${TAIRA_DIR}/requirements.txt" ]]; then
  echo "ERROR: ${TAIRA_DIR}/requirements.txt not found."
  echo "Clone/download the official master branch first:"
  echo "  git clone --branch master https://github.com/Alcein/TAIRA.git ${TAIRA_DIR}"
  exit 2
fi

if command -v conda >/dev/null 2>&1; then
  CONDA_BASE="$(conda info --base)"
  # shellcheck source=/dev/null
  source "${CONDA_BASE}/etc/profile.d/conda.sh"
  mkdir -p "${CONDA_PKGS_DIRS}"
  if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS}" conda create -n "${ENV_NAME}" "python=${PYTHON_VERSION}" -y
  fi
  conda activate "${ENV_NAME}"
else
  echo "ERROR: conda is required for the requested Python ${PYTHON_VERSION} environment."
  exit 2
fi

python -m pip install --upgrade pip
python -m pip install -r "${TAIRA_DIR}/requirements.txt"

python -c "import openai; print('openai:', openai.__version__)"
python -c "import torch; print('torch:', torch.__version__)" 2>/dev/null || echo "torch: not installed"
python -m pip list --format=freeze > "${ROOT_DIR}/results/raw_logs/env_versions.txt"

echo "Setup complete: conda env=${ENV_NAME}"
