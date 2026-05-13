#!/usr/bin/env bash
# 单脚本串行跑完全部实验（一个接一个，不并行 main.py）：
# 前置：各域已存在 TAIRA/data/<domain>/project_embeddings.npy（BGE-M3）；见 scripts/gpu_bge_offline_phase.sh。
#   LastFM 仅 PYTHONHASHSEED=2；yelp / movielens / amazon_book 各 seed 0→1→2。
# 每段 run 结束由子脚本用「与 main.py 相同」的 Python 调 parse_taira_metrics.py。
# 收尾：collect_taira_results.py（汇总 CSV）+ write_experiment_summary.md（Markdown 报告）。
#
# 用法（务必在 tmux/screen 里跑，防 SSH 断开）:
#   cd "$(git rev-parse --show-toplevel)"
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate taira
#   export TAIRA_PYTHON="$(command -v python)"
#   bash scripts/run_serial_interrec_experiments.sh
#
# 全量终端日志（可选）:
#   RUN_LOG=results/serial_run_$(date +%Y%m%d_%H%M%S).log bash scripts/run_serial_interrec_experiments.sh
# （会先 tee 到 RUN_LOG；若未设置 RUN_LOG 则默认写到 results/serial_run_<时间戳>.log）

set -euo pipefail
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

: "${TAIRA_PYTHON:=python}"
RUN_LOG="${RUN_LOG:-$REPO_ROOT/results/serial_run_$(date +%Y%m%d_%H%M%S).log}"
mkdir -p "$REPO_ROOT/results"

run_pipeline() {
  echo "[$(date -Iseconds)] TAIRA_PYTHON=$(command -v "$TAIRA_PYTHON")"
  echo "[$(date -Iseconds)] Log file: $RUN_LOG"

  echo "[$(date -Iseconds)] === Phase 1: LastFM, PYTHONHASHSEED=2 only ==="
  bash "$SCRIPT_DIR/run_lastfm_seeds.sh" 2

  echo "[$(date -Iseconds)] === Phase 2: yelp (seeds 0 1 2) ==="
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" yelp

  echo "[$(date -Iseconds)] === Phase 3: movielens (seeds 0 1 2) ==="
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" movielens

  echo "[$(date -Iseconds)] === Phase 4: amazon_book (seeds 0 1 2) ==="
  bash "$SCRIPT_DIR/run_taira_interrec_dataset.sh" amazon_book

  echo "[$(date -Iseconds)] === 汇总 CSV（collect_taira_results.py）==="
  "$TAIRA_PYTHON" "$SCRIPT_DIR/collect_taira_results.py" || true

  echo "[$(date -Iseconds)] === Markdown 报告（EXPERIMENT_SUMMARY.md）==="
  "$TAIRA_PYTHON" "$SCRIPT_DIR/write_experiment_summary.py"

  echo "[$(date -Iseconds)] 全部串行阶段结束。见: $RUN_LOG , results/taira_results.csv , results/EXPERIMENT_SUMMARY.md"
}

mkdir -p "$(dirname "$RUN_LOG")"
run_pipeline 2>&1 | tee "$RUN_LOG"
exit "${PIPESTATUS[0]}"
