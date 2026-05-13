#!/usr/bin/env bash
# Phase 1 (GPU recommended): clone/sync repo, env, precompute BGE-M3 vectors, quick test, commit + push artifacts.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# AutoDL / fat artifacts: keep npy + HF cache off the small system disk (override any of these as needed).
AUTODL_ARTIFACTS_ROOT="${AUTODL_ARTIFACTS_ROOT:-/root/autodl-tmp/interrecbaseline-TAIRA}"
export TAIRA_EMBEDDINGS_ROOT="${TAIRA_EMBEDDINGS_ROOT:-$AUTODL_ARTIFACTS_ROOT/embeddings}"
export HF_HOME="${HF_HOME:-$AUTODL_ARTIFACTS_ROOT/huggingface}"
export TMPDIR="${TMPDIR:-$AUTODL_ARTIFACTS_ROOT/tmp}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-/root/autodl-tmp/pip-cache}"
mkdir -p "$TAIRA_EMBEDDINGS_ROOT" "$HF_HOME" "$TMPDIR" "$PIP_CACHE_DIR"

# If huggingface.co is unreachable, set e.g. HF_ENDPOINT=https://hf-mirror.com before calling this script.
if [[ -n "${HF_ENDPOINT:-}" ]]; then
  export HF_ENDPOINT
  echo "    HF_ENDPOINT=$HF_ENDPOINT"
fi

echo "== TAIRA BGE offline phase (repo root: $REPO_ROOT) =="
echo "    TAIRA_EMBEDDINGS_ROOT=$TAIRA_EMBEDDINGS_ROOT"
echo "    HF_HOME=$HF_HOME"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found"
  exit 1
fi

echo "== Optional: create env =="
# python3 -m venv .venv && source .venv/bin/activate
# pip install -U pip
# pip install -r TAIRA/requirements.txt

pip install -q -r TAIRA/requirements.txt || {
  echo "ERROR: pip install failed"
  exit 1
}

echo "== Precompute embeddings (all InterRec domains) =="
python3 scripts/precompute_bge_embeddings.py --all-interrec-domains --batch-size 64

echo "== Quick test (lastfm) =="
python3 scripts/bge_offline_quick_test.py --domain lastfm

echo "== Git LFS (required if any .npy > 100MB) =="
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install
  if ! grep -q 'project_embeddings.npy' .gitattributes 2>/dev/null; then
    git lfs track 'TAIRA/data/**/project_embeddings.npy'
  fi
else
  echo "WARNING: git-lfs not installed. Large npy may be rejected by GitHub (>100MB/file)."
fi

echo "Done. Suggested next steps:"
echo "  # Git/LFS expects files under TAIRA/data/<domain>/ (embeddings are under \$TAIRA_EMBEDDINGS_ROOT):"
echo "  for d in lastfm yelp movielens amazon_book; do mkdir -p \"TAIRA/data/\$d\"; cp -a \"\$TAIRA_EMBEDDINGS_ROOT/\$d/project_embeddings.npy\" \"\$TAIRA_EMBEDDINGS_ROOT/\$d/bge_embedding_manifest.json\" \"TAIRA/data/\$d/\"; done"
echo "  git add .gitattributes TAIRA/data/*/project_embeddings.npy TAIRA/data/*/bge_embedding_manifest.json"
echo "  git commit -m \"data: BGE-M3 item embeddings (InterRec domains)\""
echo "  git push origin main"
echo "  # Phase 2 (same machine): export TAIRA_EMBEDDINGS_ROOT=\"$TAIRA_EMBEDDINGS_ROOT\""
echo "  #   export OPENAI_API_KEY=... && ./scripts/run_taira_after_bge_embeddings.sh <domain>"

