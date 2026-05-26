#!/usr/bin/env bash
# 串行跑 yelp → movielens → amazon_book（每域 3×seed，main_resume 检查点 + 每题落盘）。
# 与 Phase1 LastFM 分开，便于_LASTFM 已完成后接续。
#
# 用法（推荐 screen）:
#   cd "$(git rev-parse --show-toplevel)"
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate taira
#   export TAIRA_PYTHON="$(command -v python)"
#   bash scripts/run_yelp_movielens_amazon_serial.sh
#
# 全量日志:
#   RUN_LOG=results/three_domains_$(date +%Y%m%d_%H%M%S).log bash scripts/run_yelp_movielens_amazon_serial.sh
#
set -euo pipefail
set -o pipefail

export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f "$REPO_ROOT/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ROOT/.env.local"
  set +a
  echo "[$(date -Iseconds 2>/dev/null || date)] Loaded .env.local"
fi

: "${TAIRA_PYTHON:=python3}"
RUN_LOG="${RUN_LOG:-$REPO_ROOT/results/three_domains_$(date +%Y%m%d_%H%M%S).log}"
mkdir -p "$REPO_ROOT/results"

run_three() {
  echo "[$(date -Iseconds 2>/dev/null || date)] TAIRA_PYTHON=$(command -v "$TAIRA_PYTHON")"
  echo "[$(date -Iseconds 2>/dev/null || date)] Log: $RUN_LOG"

  echo ""
  echo "########## 1/3 yelp ##########"
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" yelp

  echo ""
  echo "########## 2/3 movielens ##########"
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" movielens

  echo ""
  echo "########## 3/3 amazon_book ##########"
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" amazon_book

  echo ""
  echo "[$(date -Iseconds 2>/dev/null || date)] === 汇总 Markdown（EXPERIMENT_SUMMARY.md）==="
  "$TAIRA_PYTHON" "$SCRIPT_DIR/write_experiment_summary.py" || true

  echo ""
  echo "[$(date -Iseconds 2>/dev/null || date)] 三域串行结束。metrics: results/metrics/ ，检查点: results/checkpoints/<域>/seed_*/result-TAIRA.csv"
}

mkdir -p "$(dirname "$RUN_LOG")"
run_three 2>&1 | tee "$RUN_LOG"
exit "${PIPESTATUS[0]}"
