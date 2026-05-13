#!/usr/bin/env bash
# Full GPU-only phase: venv (if missing) → pull BAAI/bge-m3 into BGE_M3_LOCAL_DIR →
# precompute dense vectors for all InterRec domains (lastfm, yelp, movielens, amazon_book).
# Intended for AutoDL / large-disk layouts; does not run TAIRA main experiments (no API/GPU after this).
set -euo pipefail

REPO="${TAIRA_REPO_ROOT:-/root/interrecbaseline-TAIRA}"
ROOT="${AUTODL_ARTIFACTS_ROOT:-/root/autodl-tmp/interrecbaseline-TAIRA}"
cd "$REPO"

export AUTODL_ARTIFACTS_ROOT="$ROOT"
export BGE_M3_LOCAL_DIR="${BGE_M3_LOCAL_DIR:-$ROOT/models/BAAI-bge-m3}"
export TAIRA_EMBEDDINGS_ROOT="$ROOT/embeddings"
export HF_HOME="$ROOT/huggingface"
export TMPDIR="$ROOT/tmp"
mkdir -p "$BGE_M3_LOCAL_DIR" "$TAIRA_EMBEDDINGS_ROOT" "$HF_HOME" "$TMPDIR"

LOG="$ROOT/precompute_bge.log"
RUN_TAG="bge-bundle-$(date +%s)"
VENV_PY="$REPO/.venv/bin/python"

echo "=== $(date -Is) $RUN_TAG start (repo=$REPO artifacts=$ROOT) ===" | tee -a "$LOG"

if [[ ! -x "$VENV_PY" ]]; then
  echo "=== $(date -Is) create .venv under $REPO ===" | tee -a "$LOG"
  python3 -m venv "$REPO/.venv"
  "$VENV_PY" -m pip install -U pip wheel
fi
echo "=== $(date -Is) pip install requirements ===" | tee -a "$LOG"
"$VENV_PY" -m pip install -q -r "$REPO/TAIRA/requirements.txt"

echo "=== $(date -Is) download BAAI/bge-m3 -> $BGE_M3_LOCAL_DIR ===" | tee -a "$LOG"
set +e
set +o pipefail
"$VENV_PY" -u <<'PY' 2>&1 | tee -a "$LOG"
import os
LOCAL = os.environ["BGE_M3_LOCAL_DIR"]
os.makedirs(LOCAL, exist_ok=True)
if os.path.isfile(os.path.join(LOCAL, "config.json")):
    print("BGE-M3 weights already present (config.json found), skip download")
else:
    from huggingface_hub import snapshot_download

    kw = dict(
        repo_id="BAAI/bge-m3",
        repo_type="model",
        local_dir=LOCAL,
        local_dir_use_symlinks=False,
        ignore_patterns=["**/.DS_Store", ".DS_Store", "*.DS_Store"],
    )
    saved = os.environ.pop("HF_ENDPOINT", None)
    if saved:
        print("(try official Hub first; temporarily unset HF_ENDPOINT, was %r)" % (saved,))
    try:
        snapshot_download(**kw)
        print("snapshot_download OK (official Hub)")
    except BaseException as e:
        print("official Hub failed:", type(e).__name__, e)
        mirror = saved or "https://hf-mirror.com"
        os.environ["HF_ENDPOINT"] = mirror
        print("retry with HF_ENDPOINT=", mirror)
        snapshot_download(**kw)
        print("snapshot_download OK (mirror)")
print("BGE_M3_LOCAL_DIR ready:", LOCAL)
PY
prefetch=${PIPESTATUS[0]}
set -e
set -o pipefail
if [[ "$prefetch" -ne 0 ]]; then
  echo "=== $(date -Is) $RUN_TAG ERROR: download exit $prefetch ===" | tee -a "$LOG"
  exit "$prefetch"
fi

if [[ ! -f "$BGE_M3_LOCAL_DIR/config.json" ]]; then
  echo "=== $(date -Is) $RUN_TAG ERROR: missing $BGE_M3_LOCAL_DIR/config.json ===" | tee -a "$LOG"
  exit 2
fi

echo "=== $(date -Is) encode (CUDA required) load_path=$BGE_M3_LOCAL_DIR ===" | tee -a "$LOG"
if ! "$VENV_PY" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then
  echo "=== $(date -Is) $RUN_TAG ERROR: CUDA required for precompute ===" | tee -a "$LOG"
  exit 3
fi

set +e
set +o pipefail
"$VENV_PY" "$REPO/scripts/precompute_bge_embeddings.py" \
  --all-interrec-domains --batch-size 64 --model "$BGE_M3_LOCAL_DIR" 2>&1 | tee -a "$LOG"
code=${PIPESTATUS[0]}
set -e
set +o pipefail

echo "=== $(date -Is) $RUN_TAG finished exit_code=$code ===" | tee -a "$LOG"
exit "$code"
